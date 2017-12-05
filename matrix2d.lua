-- info-beamer matrix2d
--
-- Copyright (c) 2017 Florian Wesch <fw@dividuum.de>
-- This code is BSD-2 licenced: http://opensource.org/licenses/BSD-2-Clause

local sin, cos, pi = math.sin, math.cos, math.pi
local setmetatable = setmetatable

local mt; mt = {
    __call = function (self, x, y)
        return self.v11*x + self.v12*y + self.v13,
               self.v21*x + self.v22*y + self.v23
   end;
    __mul = function(a, b)
        return setmetatable({
            v11 = a.v11*b.v11 + a.v12*b.v21 + a.v13*b.v31; 
            v12 = a.v11*b.v12 + a.v12*b.v22 + a.v13*b.v32;
            v13 = a.v11*b.v13 + a.v12*b.v23 + a.v13*b.v33;
            v21 = a.v21*b.v11 + a.v22*b.v21 + a.v23*b.v31;
            v22 = a.v21*b.v12 + a.v22*b.v22 + a.v23*b.v32;
            v23 = a.v21*b.v13 + a.v22*b.v23 + a.v23*b.v33;
            v31 = a.v31*b.v11 + a.v32*b.v21 + a.v33*b.v31;
            v32 = a.v31*b.v12 + a.v32*b.v22 + a.v33*b.v32;
            v33 = a.v31*b.v13 + a.v32*b.v23 + a.v33*b.v33;
        }, mt)
    end;
    __unm = function(self)
        local det = self.v11 * (self.v22 * self.v33 - self.v32 * self.v23) -
                    self.v12 * (self.v21 * self.v33 - self.v23 * self.v31) +
                    self.v13 * (self.v21 * self.v32 - self.v22 * self.v31)
        local invdet = 1 / det
        return setmetatable({
            v11 = (self.v22 * self.v33 - self.v32 * self.v23) * invdet;
            v12 = (self.v13 * self.v32 - self.v12 * self.v33) * invdet;
            v13 = (self.v12 * self.v23 - self.v13 * self.v22) * invdet;
            v21 = (self.v23 * self.v31 - self.v21 * self.v33) * invdet;
            v22 = (self.v11 * self.v33 - self.v13 * self.v31) * invdet;
            v23 = (self.v21 * self.v13 - self.v11 * self.v23) * invdet;
            v31 = (self.v21 * self.v32 - self.v31 * self.v22) * invdet;
            v32 = (self.v31 * self.v12 - self.v11 * self.v32) * invdet;
            v33 = (self.v11 * self.v22 - self.v21 * self.v12) * invdet;
        }, mt)
    end;
    __tostring = function(self)
        return string.format("|%12.5f,%12.5f,%12.5f|\n|%12.5f,%12.5f,%12.5f|\n|%12.5f,%12.5f,%12.5f|",
               self.v11, self.v12, self.v13,
               self.v21, self.v22, self.v23,
               self.v31, self.v32, self.v33
       )
    end;
    __index = {
        adjugate = function(self)
            return setmetatable({
                v11 = self.v22 * self.v33 - self.v32 * self.v23;
                v12 = self.v13 * self.v32 - self.v12 * self.v33;
                v13 = self.v12 * self.v23 - self.v13 * self.v22;
                v21 = self.v23 * self.v31 - self.v21 * self.v33;
                v22 = self.v11 * self.v33 - self.v13 * self.v31;
                v23 = self.v21 * self.v13 - self.v11 * self.v23;
                v31 = self.v21 * self.v32 - self.v31 * self.v22;
                v32 = self.v31 * self.v12 - self.v11 * self.v32;
                v33 = self.v11 * self.v22 - self.v21 * self.v12;
            }, mt)
        end;
        mult_vec3 = function(self, x, y, z)
            return self.v11*x + self.v12*y + self.v13,
                   self.v21*x + self.v22*y + self.v23,
                   self.v31*x + self.v32*y + self.v33
        end;
    }
}

local function new(v11, v12, v13, v21, v22, v23, v31, v32, v33)
    return setmetatable({
        v11 = v11; v12 = v12; v13 = v13;
        v21 = v21; v22 = v22; v23 = v23;
        v31 = v31; v32 = v32; v33 = v33;
    }, mt)
end

local function trans(dx,dy)
    return new(
        1, 0, dx,
        0, 1, dy,
        0, 0,  1
    )
end

local function ident()
    return trans(0,0)
end

local function rotate(rot)
    return new(
        cos(rot), -sin(rot), 0,
        sin(rot),  cos(rot), 0,
               0,         0, 1
    )
end

local function rotate_deg(rot)
    return rotate(rot / 180 * pi)
end

local function scale(sx,sy)
    return new(
        sx,  0, 0,
         0, sy, 0,
         0,  0, 1
    )
end

return {
    new = new,
    trans = trans,
    ident = ident,
    scale = scale,
    rotate = rotate,
    rotate_deg = rotate_deg,
}
