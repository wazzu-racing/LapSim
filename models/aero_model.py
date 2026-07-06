

class Aero:

    def __init__(self, racecar):
        self.racecar = racecar

        self.F_drag = 41 # lbs at speed
        self.F_down = 105 # lbs at speed
        self.speed = 616 # in/s
        self.P_air = 4.43e-5 # lbs/in^3
        self.COP_X = 6 # inches, behind CG

        self.C_drag = 2 * self.F_drag / (self.P_air * self.speed**2)
        self.C_down = 2 * self.F_down / (self.P_air * self.speed**2)

    # returns drag in lbs
    # Speed = in/s
    def get_drag(self, speed):
        return 1/2 * self.P_air * self.C_drag * speed**2

    # returns downforce in lbs, front axle and rear axle
    # Speed = in/s
    def get_down(self, speed):
        FULL_DOWN = 1/2 * self.P_air * self.C_down * speed**2
        D_f = FULL_DOWN * ((self.racecar.b-self.COP_X)/self.racecar.l)
        D_r = FULL_DOWN * ((self.racecar.b+self.COP_X)/self.racecar.l)
        return D_f, D_r