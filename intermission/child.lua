local api, CHILDS, CONTENTS = ...

math.randomseed(os.time())

local max = math.max

local M = {}

local files = {}
local num_pictures = 0

local function shuffle(tbl)
    local size = #tbl
    for i = size, 1, -1 do
        local rand = math.random(size)
        tbl[i], tbl[rand] = tbl[rand], tbl[i]
    end
    return tbl
end

function M:load_next_image()
    local file = files[self.image_offset]
    self.image_offset = self.image_offset % #files + 1
    self.next_image = resource.load_image(file:copy())
end

function M:slot_time()
    return max(0.5, self.duration)
end

function M:prepare()
    print "child prepare"
    shuffle(files)

    self.image_offset = 1
    self.per_image_time = self.duration / num_pictures
    self.next_switch = self.t_start

    self:load_next_image()
end

function M:tick(now)
    if now > self.next_switch then
        self.image = self.next_image
        self:load_next_image()
        self.next_switch = now + self.per_image_time
    end
    util.draw_correct(self.image, 0, 0, WIDTH, HEIGHT)
end

function M:stop()
    print "child stop"
    if self.next_image then
        self.next_image:dispose()
    end
    self.image:dispose()
end

function M.updated_config_json(config)
    print("child config.json UPDATE!")
    local new_files = {}
    for idx = 1, #config.pictures do
        new_files[idx] = resource.open_file(api.localized(
            config.pictures[idx].file.asset_name
        ))
    end
    pp(new_files)

    -- all files open? then proceed to switch
    files = new_files
    num_pictures = config.num_pictures
end

return M
