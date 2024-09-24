from enum import Enum


class Building(Enum):
    ANAC = 'ANAC'
    CDC = 'CDC'
    DC = 'DC'
    ECS = 'ECS'
    EN2 = 'EN2'
    EN3 = 'EN3'
    EN4 = 'EN4'
    EN5 = 'EN5'
    ET = 'ET'
    HSCI = 'HSCI'
    NUR = 'NUR'
    VEC = 'VEC'


class Schedule(Enum):
    MW = 'MW'
    TuTh = 'TuTh'
    MWF = 'MWF'
    F = 'F'
    S = 'S'


class Semester(Enum):
    Fall = 'Fall'
    Spring = 'Spring'
    Summer_I = 'Summer I'
    Summer_II = 'Summer II'
    Summer_III = 'Summer III'
    Winter = 'Winter'


class MinimumSatisfactory(Enum):
    A = 'A'
    B = 'B'
    C = 'C'