gl.setup(NATIVE_WIDTH, NATIVE_HEIGHT)

util.noglobals()

-- We need to access files in screens/
node.make_nested()

-- Start preloading images this many second before
-- they are displayed.
local PREPARE_TIME = 1 -- seconds

-- must be enough time to load a video and have it
-- ready in the paused state. Normally 500ms should
-- be enough.
local VIDEO_PRELOAD_TIME = .5 -- seconds

local json = require "json"
local matrix = require "matrix2d"
local font = resource.load_font "silkscreen.ttf"
local serial = sys.get_env "SERIAL"
local min, max = math.min, math.max

local assigned = false
local delta_t = 0
local adjust = false

local function msg(str, ...)
    font:write(10, 10, str:format(...), 24, 1,1,1,.5)
    print(str:format(...))
end

local function get_walltime()
    return os.time() + max(-1000, min(1000, delta_t))/1000
end

local function Screen()
    local content_w, content_h
    local screen
    local virtual2pixel

    local function update(new_screen, new_content_w, new_content_h)
        screen = new_screen
        content_w, content_h = new_content_w, new_content_h

        virtual2pixel = 
               matrix.scale(WIDTH / content_w,
                            HEIGHT / content_h) *
               matrix.scale(content_w / screen.width,
                            content_h / screen.height) *
               matrix.trans(-screen.x, -screen.y) 
    end

    local function screen_coordinates(obj)
        local x1, y1 = 0, 0
        local x2, y2 = content_w, content_h
        if adjust then
            local _, w, h = obj:state()
            x1, y1, x2, y2 = util.scale_into(content_w, content_h, w, h)
        end
        local s_x1, s_y1 = virtual2pixel(x1, y1)
        local s_x2, s_y2 = virtual2pixel(x2, y2)
        return s_x1, s_y1, s_x2, s_y2
    end

    local function draw_image(obj)
        local x1, y1, x2, y2 = screen_coordinates(obj)
        obj:draw(x1, y1, x2, y2)
    end

    local function draw_video(obj)
        local x1, y1, x2, y2 = screen_coordinates(obj)
        obj:place(x1, y1, x2, y2, 0):layer(1)
    end

    return {
        update = update;
        draw_image = draw_image;
        draw_video = draw_video;
    }
end

local screen = Screen()

local Image = {
    slot_time = function(self)
        return max(0.5, self.duration)
    end;
    prepare = function(self)
        self.obj = resource.load_image(self.file:copy())
    end;
    tick = function(self, now)
        local state, w, h = self.obj:state()
        screen.draw_image(self.obj)
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
        return VIDEO_PRELOAD_TIME + max(0.5, self.duration)
    end;
    prepare = function(self)
    end;
    tick = function(self, now)
        if not self.obj then
            self.obj = resource.load_video{
                file = self.file:copy();
                raw = true,
                paused = true;
            }
        end

        if now < self.t_start + VIDEO_PRELOAD_TIME then
            return
        end

        self.obj:start()
        local state, w, h = self.obj:state()

        if state ~= "loaded" and state ~= "finished" then
            print[[

.--------------------------------------------.
  WARNING:
  lost video frame. video is most likely out
  of sync. increase VIDEO_PRELOAD_TIME (on all
  devices)
'--------------------------------------------'
]]
        else
            screen.draw_video(self.obj)
        end
    end;
    stop = function(self)
        if self.obj then
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
        pp(item)
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

        for idx = 1, #items do
            local item = items[idx]

            if item.state == "new" then
                calc_start(idx, now)
                item.state = "waiting"
            end

            if item.t_prepare <= now and item.state == "waiting" then
                print(now, "preparing ", item.file)
                item:prepare()
                item.state = "prepared"
            elseif item.t_start <= now and item.state == "prepared" then
                print(now, "running ", item.file)
                item.state = "running"
            elseif item.t_end <= now and item.state == "running" then
                print(now, "resetting ", item.file)
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
            screen.update(screen_config, config.width, config.height)
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
        items[#items+1] = {
            file = resource.open_file(item.file.asset_name),
            type = item.file.type,
            duration = item.duration,
        }
    end
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
