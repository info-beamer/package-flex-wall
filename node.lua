-- License: BSD 2 clause (see LICENSE.txt)
gl.setup(NATIVE_WIDTH, NATIVE_HEIGHT)

util.no_globals()

-- We need to access files in screens/
node.make_nested()

-- Start preloading images/videos this many second before
-- they are displayed.
local PREPARE_TIME = 1.5 -- seconds

-------------------------------------------------------------

local json = require "json"
local matrix = require "matrix2d"
local font = resource.load_font "silkscreen.ttf"
local serial = sys.get_env "SERIAL"
local min, max = math.min, math.max

local assigned = false
local delta_t = 0
local adjust = false
local effect = "none"
local audio = false
local fallback 
local status_text = "top_left"

local function clamp(v, min, max)
    return math.max(min, math.min(max, v))
end

local function round(v)
    return math.floor(v+.5)
end

local function expand_schedule(config, schedule)
    if schedule == 'always' or schedule == 'never' then
        return schedule
    end
    return config.__schedules.expanded[schedule+1]
end

local function is_schedule_active_at(schedule, probe_time)
    if schedule == "always" then
        return true
    elseif schedule == "never" then
        return false
    end
    if probe_time < 10000000 then
        return false -- no valid system time, don't schedule
    end
    for _, range in ipairs(schedule) do
        local starts, duration = unpack(range)
        if starts > probe_time then
            break
        elseif probe_time < starts + duration then
            return true
        end
    end
    return false
end

local function printf(fmt, ...)
    return print(string.format(fmt, ...))
end

local function msg(str, ...)
    local text = str:format(...)
    if status_text == "off" then
        return
    end
    local size = 24
    local width = font:width(text, size)
    local x, y = unpack(({
        top_left = {10, 10},
        top_right = {NATIVE_WIDTH - 10 - width, 10},
        bottom_left = {10, NATIVE_HEIGHT - 10 - size},
        bottom_right = {NATIVE_WIDTH - 10 - width, NATIVE_HEIGHT - 10 - size},
    })[status_text])
    font:write(x, y, text, size, 1,1,1,.5)
end

local function get_walltime()
    return os.time() + max(-1000, min(1000, delta_t))/1000
end

local function ramp(t_s, t_e, t_c, ramp_time)
    if ramp_time == 0 then return 1 end
    local delta_s = t_c - t_s
    local delta_e = t_e - t_c
    return math.min(1, delta_s * 1/ramp_time, delta_e * 1/ramp_time)
end

local function get_alpha(starts, ends, now)
    local alpha
    if effect == "none" then
        alpha = 1
    elseif effect == "fade_02" then
        alpha = ramp(starts, ends, now, 0.2)
    elseif effect == "fade_05" then
        alpha = ramp(starts, ends, now, 0.5)
    end
    return alpha
end

local function VirtualScreen()
    local screen, virtual2pixel, pixel2virtual
    local virtual_w, virtual_h
    local translate_0_x, translate_0_y
    local scale_x, scale_y

    local function update(new_screen)
        screen = new_screen

        gl.setup(NATIVE_WIDTH, NATIVE_HEIGHT)
        virtual_w, virtual_h = screen.res_x or NATIVE_WIDTH,
                               screen.res_y or NATIVE_HEIGHT

        scale_x = NATIVE_WIDTH / virtual_w
        scale_y = NATIVE_HEIGHT / virtual_h

        if screen.rotation == 0 then
            translate_0_x, translate_0_y = 0, 0
        elseif screen.rotation == 90 then
            translate_0_x, translate_0_y = WIDTH, 0
            virtual_w, virtual_h = virtual_h, virtual_w
        elseif screen.rotation == 180 then
            translate_0_x, translate_0_y = WIDTH, HEIGHT
        elseif screen.rotation == 270 then
            translate_0_x, translate_0_y = 0, HEIGHT
            virtual_w, virtual_h = virtual_h, virtual_w
        end

        WIDTH = virtual_w
        HEIGHT = virtual_h

        virtual2pixel = matrix.trans(translate_0_x, translate_0_y)
                      * matrix.scale(scale_x, scale_y)
                      * matrix.rotate_deg(screen.rotation)
        pixel2virtual = -virtual2pixel
    end

    local function project(x1, y1, x2, y2)
        x1, y1 = virtual2pixel(x1, y1)
        x2, y2 = virtual2pixel(x2, y2)
        return math.floor(math.min(x1, x2)), math.floor(math.min(y1, y2)),
               math.floor(math.max(x1, x2)), math.floor(math.max(y1, y2))
    end

    local function unproject(x, y)
        x, y = pixel2virtual(x, y)
        return math.floor(x), math.floor(y)
    end

    local function video(vid, x1, y1, x2, y2, layer, alpha)
        layer = layer or 1
        x1, y1, x2, y2 = project(x1, y1, x2, y2)
        return vid:alpha(alpha):place(
            x1, y1, x2, y2, screen.rotation
        ):layer(layer)
    end

    local function setup()
        gl.translate(translate_0_x, translate_0_y)
        gl.scale(scale_x, scale_y)
        gl.rotate(screen.rotation, 0, 0, 1)
    end

    return {
        update = update;
        unproject = unproject;
        setup = setup;
        video = video;
    }
end

local function ContentArea(screen)
    local content_w, content_h
    local content_area
    local content2virtual

    local function update(new_content_area, new_content_w, new_content_h)
        screen.update{
            rotation = new_content_area.rotation,
        }

        content_area = new_content_area
        content_w, content_h = new_content_w, new_content_h

        content2virtual = matrix.scale(WIDTH / content_w,
                                       HEIGHT / content_h)
                        * matrix.scale(content_w / content_area.width,
                                       content_h / content_area.height)
                        * matrix.trans(-content_area.x, -content_area.y)
    end

    local function virtual_coordinates(obj)
        local x1, y1 = 0, 0
        local x2, y2 = content_w, content_h
        if adjust then
            local _, w, h = obj:state()
            x1, y1, x2, y2 = util.scale_into(content_w, content_h, w, h)
        end
        x1, y1 = content2virtual(x1, y1)
        x2, y2 = content2virtual(x2, y2)
        return x1, y1, x2, y2
    end

    local function draw_image(obj, a)
        local x1, y1, x2, y2 = virtual_coordinates(obj)
        gl.pushMatrix()
            screen.setup()
            obj:draw(x1, y1, x2, y2, a)
        gl.popMatrix()
    end

    local function draw_video(obj, a)
        local x1, y1, x2, y2 = virtual_coordinates(obj)
        screen.video(obj, x1, y1, x2, y2, 1, a)
    end

    return {
        update = update;
        draw_image = draw_image;
        draw_video = draw_video;
    }
end

local content_area = ContentArea(VirtualScreen())

local Image = {
    prepare = function(self)
        self.obj = resource.load_image(self.file:copy())
    end;
    tick = function(self, now)
        local state, w, h = self.obj:state()
        if state == "loading" then
            print "WARNING: lost image frame. image not loaded in time."
        elseif state == "error" then
            msg(w)
            printf("Cannot load image: %s", w)
        else
            local alpha = get_alpha(
                self.t_start, self.t_end, now
            )
            content_area.draw_image(self.obj, alpha)
        end
    end;
    stop = function(self)
        if self.obj then
            self.obj:dispose()
            self.obj = nil
        end
    end;
}

local Video = {
    prepare = function(self)
        self.obj = resource.load_video{
            file = self.file:copy(),
            raw = true,
            paused = true,
            looped = true,
            audio = audio,
        }:alpha(0):layer(-1)
    end;
    tick = function(self, now)
        self.obj:start()
        local state, w, h = self.obj:state()

        if state == "loading" then
            print "WARNING: lost video frame. video is most likely out of sync."
        elseif state == "error" then
            msg(w)
            printf("Cannot load video: %s", w)
        else
            local alpha = get_alpha(
                self.t_start, self.t_end, now
            )
            content_area.draw_video(self.obj, alpha)
        end
    end;
    stop = function(self)
        if self.obj then
            self.obj:layer(-1)
            self.obj:dispose()
            self.obj = nil
        end
    end;
}

local function Playlist()
    local all_items = {}
    local function set(new_items)
        all_items = new_items
    end

    local function make_instance(item)
        local instance = {}
        for k, v in pairs(item) do
            instance[k] = v
        end
        setmetatable(instance, {__index = ({
            image = Image,
            video = Video,
        })[instance.filetype]})
        return instance
    end

    local function get_next(test_t, back)
        local scheduled_items = {}
        for idx, item in ipairs(all_items) do
            if is_schedule_active_at(item.schedule, test_t) then
                scheduled_items[#scheduled_items+1] = item
            end
        end

        if #scheduled_items == 0 then
            scheduled_items[1] = {
                file = fallback:copy(),
                filetype = "image",
                duration = 2,
                schedule = "always",
            }
        end

        local total_duration = 0
        for idx, item in ipairs(scheduled_items) do
            item.epoch_offset = total_duration
            local duration = item.duration
            total_duration = total_duration + item.duration
        end

        local epoch_offset = test_t % total_duration
        local epoch_start = test_t - epoch_offset

        local next_start, next_idx
        for idx, item in ipairs(scheduled_items) do
            local start_t = epoch_start + item.epoch_offset
            if start_t >= test_t then
                next_start = start_t
                next_idx = idx
                break
            end
        end

        if not next_start then
            -- None matched. This only happens if the test
            -- time is after the last item's start time (so
            -- the item is playing right now). In that
            -- case the next item will be the first again.
            next_start = epoch_start + total_duration
            next_idx = 1
        end

        -- If requested, walk backwards in time, adjusting start
        -- time and item.
        back = back or 0
        while back > 0 do
            next_idx = (next_idx - 2) % #scheduled_items + 1
            next_start = next_start - scheduled_items[next_idx].duration
            back = back - 1
        end

        local player = make_instance(scheduled_items[next_idx])
        player.t_start = next_start
        player.t_end = player.t_start + player.duration
        return next_start, player
    end

    return {
        set = set;
        get_next = get_next;
    }
end

local function PlaylistPlayer(playlist)
    local cur, nxt
    local switch
    local reschedule = get_walltime()

    local function tick(now)
        if not assigned then
            msg("[%s] screen not configured for this setup", serial)
            return
        end

        if not nxt and now >= reschedule then
            if not cur then
                -- While starting, check if the currently playing item
                -- would be an image. If so, allow scheduling it late.
                local past_switch, maybe_nxt = playlist.get_next(reschedule, 1)
                if maybe_nxt.filetype == "image" then
                    printf('late starting image. missed %.3fs', now - past_switch)
                    switch = past_switch
                    nxt = maybe_nxt
                end
            end
            if not nxt then
                switch, nxt = playlist.get_next(reschedule)
            end
            printf('next in %.5fs', switch - now)
            pp(nxt)
            nxt:prepare()
        end

        if nxt and switch and now >= switch then
            print('switch to')
            pp(nxt)
            local old = cur
            cur = nxt
            nxt = nil
            reschedule = max(now, switch + cur.duration - PREPARE_TIME)
            if old then
                old:stop()
            end
        end

        if cur then
            cur:tick(now)
        else
            local wait = switch - now
            msg(("Waiting for sync %.1f"):format(wait))
        end
    end

    return {
        tick = tick;
    }
end

local playlist = Playlist()
local playlist_player = PlaylistPlayer(playlist)

util.json_watch("screens/config.json", function(config)
    adjust = config.adjust
    status_text = config.status_text
    delta_t = 0
    assigned = false

    for idx, screen_config in ipairs(config.screens) do
        if screen_config.serial == serial then
            content_area.update(screen_config, config.width, config.height)
            delta_t = screen_config.delta_t
            assigned = true
            return
        end
    end
end)

util.json_watch("config.json", function(config)
    effect = config.effect
    audio = config.audio
    fallback = resource.open_file(config.fallback.asset_name)

    local items = {}
    local configured_playlist = config.playlist or {}
    for idx, item in ipairs(configured_playlist) do
        if item.duration > 0 then
            items[#items+1] = {
                file = resource.open_file(item.file.asset_name),
                filetype = item.file.type,
                duration = max(1, item.duration),
                schedule = expand_schedule(config, item.schedule),
            }
        end
    end
    playlist.set(items)
    node.gc()
end)

function node.render()
    gl.clear(0, 0, 0, 1)
    playlist_player.tick(get_walltime())
end
