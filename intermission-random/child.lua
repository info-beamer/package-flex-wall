local api, CHILDS, CONTENTS = ...

local max = math.max

local M = {}

local assets = {}
local randomize_playtime = 0

local function shuffle(tbl)
    local size = #tbl
    for i = size, 1, -1 do
        local rand = math.random(size)
        tbl[i], tbl[rand] = tbl[rand], tbl[i]
    end
    return tbl
end

function M:load_next_item()
    local item = assets[self.offset]
    self.offset = self.offset % #assets + 1

    local duration = max(
        1, item.duration + (math.random()-0.5) * randomize_playtime
    )

    if item.type == "image" then
        self.next_player = {
            obj = resource.load_image(item.file:copy()),
            type = "image",
            duration = duration,
        }
    else
        self.next_player = {
            obj = resource.load_video{
                file = item.file:copy(),
                raw = true,
                paused = true,
                looped = true,
            },
            type = "video",
            duration = duration,
        }
    end
end

function M:slot_time()
    return max(0.5, self.duration)
end

function M:prepare()
    shuffle(assets)

    self.offset = 1
    self.next_switch = self.t_start
    self.player = nil

    self:load_next_item()
end

function M:tick(now)
    if now > self.next_switch then
        if self.player then
            self.player.obj:dispose()
        end
        self.player = self.next_player
        if self.player.type == "video" then
            local state, width, height = self.player.obj:state()
            self.player.obj:place(util.scale_into(
                WIDTH, HEIGHT, width, height
            )):layer(10):start()
        end
        self:load_next_item()
        self.next_switch = now + self.player.duration
    end
    if self.player.type == "image" then
        util.draw_correct(self.player.obj, 0, 0, WIDTH, HEIGHT)
    end
end

function M:stop()
    if self.next_player then
        self.next_player.obj:dispose()
    end
    self.player.obj:dispose()
end

function M.updated_config_json(config)
    print("child config.json UPDATE!")
    local new_assets = {}
    for idx = 1, #config.playlist do
        local item = config.playlist[idx]
        new_assets[idx] = {
            file = resource.open_file(api.localized(
                item.file.asset_name
            )),
            type = item.file.type,
            duration = item.duration,
        }
    end

    -- all files open? then proceed to switch
    randomize_playtime = config.randomize_playtime
    assets = new_assets
end

return M
