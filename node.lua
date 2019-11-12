-- prevent accidental global variables
util.no_globals()

-- We need to access files in screens/
node.make_nested()

-- Start preloading images this many second before
-- they are displayed.
local PREPARE_TIME = 1 -- seconds

-- There is only one HEVC decoder slot. So videos
-- cannot be preloaded. Instead we reserve the
-- following number of seconds at each play slot
-- for loading the video.
local HEVC_LOAD_TIME = 0.5 -- seconds

-- Each playslot must be at least this long.
-- Otherwise prepare time completely skips the
-- previous slot.
local MIN_DURATION = 1.2 -- seconds

local json = require "json"
local matrix = require "matrix2d"
local font = resource.load_font "silkscreen.ttf"
local serial = sys.get_env "SERIAL"
local min, max = math.min, math.max

local assigned = false
local delta_t = 0
local adjust = false
local effect = "none"
local preload_time = 0.5

local function msg(str, ...)
    font:write(10, 10, str:format(...), 24, 1,1,1,.5)
    print(str:format(...))
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

local function get_effect_vars(starts, ends, now)
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

local Image = {
    slot_time = function(self)
        return max(MIN_DURATION, self.duration)
    end;
    prepare = function(self)
        self.obj = resource.load_image(self.file:copy())
    end;
    tick = function(self, now)
        local state, w, h = self.obj:state()
        local alpha = get_effect_vars(
            self.t_start, self.t_end, now
        )
        content_area.draw_image(self.obj, alpha)
    end;
    stop = function(self)
        if self.obj then
            self.obj:dispose()
            self.obj = nil
        end
    end;
}

local Video = {
    slot_time = function(self)
        self.preload_time = self.is_hevc and HEVC_LOAD_TIME or preload_time
        return self.preload_time + max(MIN_DURATION, self.duration)
    end;
    prepare = function(self)
        if self.preload_time == 0 then
            print "preloading video"
            self.obj = resource.load_video{
                file = self.file:copy(),
                raw = true,
                paused = true,
            }:alpha(0):layer(-1)
        end
    end;
    tick = function(self, now)
        if not self.obj then
            print "late loading video"
            self.obj = resource.load_video{
                file = self.file:copy(),
                raw = true,
                paused = true,
            }:alpha(0):layer(-1)
        end

        if now < self.t_start + self.preload_time then
            return
        end

        self.obj:start()

        local state, w, h = self.obj:state()
        if state ~= "loaded" and state ~= "finished" then
            print "lost video frame"
        else
            local alpha = get_effect_vars(
                self.t_start + self.preload_time, self.t_end, now
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
    local items = {}
    local total_duration = 0

    local function calc_start(idx, now)
        local item = items[idx]
        local epoch_offset = now % total_duration
        local epoch_start = now - epoch_offset

        item.t_start = epoch_start + item.epoch_offset
        if item.t_start - PREPARE_TIME < now then
            item.t_start = item.t_start + total_duration
        end
        item.t_prepare = item.t_start - PREPARE_TIME
        item.t_end = item.t_start + item:slot_time()
        -- pp(item)
    end

    local function tick(now)
        local is_synced = false
        local next_running = 999999999999

        if not assigned then
            msg("[%s] screen not configured for this setup", serial)
            return
        end

        if #items == 0 then
            msg("[%s] no playlist configured", serial)
            return
        end

        for idx = #items, 1, -1 do
            local item = items[idx]

            if item.state == "new" then
                print(now, "state: waiting", item.file)
                calc_start(idx, now)
                item.state = "waiting"
            end

            if now >= item.t_prepare and item.state == "waiting" then
                print(now, "state: preparing ", item.file)
                item:prepare()
                item.state = "prepared"
            elseif now >= item.t_start and item.state == "prepared" then
                print(now, "state: running ", item.file)
                item.state = "running"
            elseif now >= item.t_end and item.state == "running" then
                print(now, "state: resetting ", item.file)
                item:stop()
                calc_start(idx, now)
                item.state = "waiting"
            end

            next_running = min(next_running, item.t_start)

            if item.state == "running" then
                item:tick(now)
                is_synced = true
            end
        end

        if not is_synced then
            local wait = next_running - now
            msg("[%s] waiting for sync %.1f", serial, wait)
        end
    end

    local function stop_all()
        for idx = 1, #items do
            local item = items[idx]
            item:stop()
        end
    end

    local function set(new_items)
        total_duration = 0
        for idx = 1, #new_items do
            local item = new_items[idx]
            if item.type == "image" then
                setmetatable(item, {__index = Image})
            elseif item.type == "video" then
                setmetatable(item, {__index = Video})
            else
                return error("unsupported type" .. item.type)
            end
            item.epoch_offset = total_duration
            item.state = "new"
            total_duration = total_duration + item:slot_time()
        end

        stop_all()

        items = new_items
    end

    return {
        set = set;
        tick = tick;
    }
end

local playlist = Playlist()

local function prepare_playlist(playlist)
    if #playlist >= 2 then
        return playlist
    elseif #playlist == 1 then
        -- only a single item? Copy it
        local item = playlist[1]
        playlist[#playlist+1] = {
            file = item.file,
            type = item.type,
            duration = item.duration,
            is_hevc = item.is_hevc,
        }
    end
    return playlist
end

util.file_watch("screens/config.json", function(raw)
    local config = json.decode(raw)
    adjust = config.adjust
    delta_t = 0
    assigned = false

    for idx = 1, #config.screens do
        local screen_config = config.screens[idx]
        if screen_config.serial == serial then
            content_area.update(screen_config, config.width, config.height)
            delta_t = screen_config.delta_t
            assigned = true
            return
        end
    end
end)

util.file_watch("config.json", function(raw)
    local config = json.decode(raw)
    local items = {}
    for idx = 1, #config.playlist do
        local item = config.playlist[idx]
        local is_hevc = item.file.metadata and item.file.metadata.format == "hevc"
        items[#items+1] = {
            file = resource.open_file(item.file.asset_name),
            type = item.file.type,
            duration = item.duration,
            is_hevc = is_hevc,
        }
    end

    effect = config.effect
    preload_time = config.video_mode == "seamless" and 0 or 0.5

    playlist.set(prepare_playlist(items))
    node.gc()
end)

function node.render()
    gl.clear(0,0,0,1)

    local now = get_walltime()
    if now < 1000000 then
        msg "waiting for correct time"
    else
        playlist.tick(now)
    end
end
