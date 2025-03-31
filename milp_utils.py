# MILP class to take advantage of the previous solutions
# @tiago.silveira
# 11-30-2021

"""
This code defines a class called MILP_Variables, which is used to store and
manipulate variables related to Mixed-Integer Linear Programming (MILP) problem
"""


class MILP_Variables:
    def __init__(self):
        self.x = []

    # Set variables for 4 arcs
    def set4arcsVariables(self, x, y, r, L_sub, W_sub, delta, ii, jj,
                          z=[], qh=[], qv=[]):
        self.x = x
        self.y = y
        self.r = r
        self.L_sub = L_sub
        self.W_sub = W_sub
        self.delta = delta
        self.ii = ii
        self.jj = jj
        if len(z) > 0:
            self.z = z
        if len(qh) > 0:
            self.qh = qh
        if len(qv) > 0:
            self.qv = qv

    # Set variables for 5 arcs
    def set5arcsVariables(self, x, L_sub, W_sub, delta, ii, jj, z, qh, qv,
                          beta=[]):
        self.x = x
        self.L_sub = L_sub
        self.W_sub = W_sub
        self.delta = delta
        self.ii = ii
        self.jj = jj
        self.z = z
        self.qh = qh
        self.qv = qv
        if len(beta) > 0:
            self.beta = beta

    # Boolean Method
    def has_variables(self):
        return len(self.x) > 0

    # ----------------------------------------------------------------#
    # Initialize the variables of the model with a previous solution #
    # ----------------------------------------------------------------#
    def copy_from_previous_4arcsmodel(self, model, x, y, r, L_sub, W_sub,
                                      delta, z=[], qh=[], qv=[]):
        # Starting with 0
        model.start = [(r, self.r)]

        for j in self.jj:
            model.start = [(x[j], self.x[j])]
            model.start = [(y[j], self.y[j])]
            model.start = [(L_sub[j], self.L_sub[j])]
            model.start = [(W_sub[j], self.W_sub[j])]

            if len(z) > 0:
                model.start = [(z[j], self.z[j])]

        for i in self.ii:
            for j in self.jj:
                model.start = [(delta[i][j], self.delta[i][j])]
                if len(qh) > 0:
                    model.start = [(qh[i][j], self.qh[i][j])]
                if len(qv) > 0:
                    model.start = [(qv[i][j], self.qv[i][j])]

    def copy_from_previous_5arcsmodel(self, model, x, L_sub, W_sub, delta, z,
                                      qh, qv, beta=[]):
        # Start with 0
        for j in self.jj:
            model.start = [(x[j], self.x[j])]
            model.start = [(L_sub[j], self.L_sub[j])]
            model.start = [(W_sub[j], self.W_sub[j])]
            model.start = [(z[j], self.z[j])]

            if len(beta) > 0:
                model.start = [(beta[j], self.beta[j])]

        for i in self.ii:
            for j in self.jj:
                model.start = [(delta[i][j], self.delta[i][j])]
                model.start = [(qh[i][j], self.qh[i][j])]
                model.start = [(qv[i][j], self.qv[i][j])]

    # -----------------------------------------------------------#
    # Initialize the model variables with a predefined solution #
    # -----------------------------------------------------------#
    @staticmethod
    def test4arcs(model, x, y, r, L_sub, W_sub, delta, ii, jj, z=[],
                  qh=[], qv=[]):
        # Start with 0
        model.start = [(r, 0)]

        for j in jj:
            model.start = [(x[j], 0)]
            model.start = [(y[j], 0)]
            model.start = [(L_sub[j], 0)]
            model.start = [(W_sub[j], 0)]

        for i in ii:
            for j in jj:
                model.start = [(delta[i][j], 0)]

        # SLOPP
        if len(z) > 0:
            for j in jj:
                model.start = [(z[j], 0)]

            for i in ii:
                for j in jj:
                    model.start = [(qv[i][j], 0)]
                    model.start = [(qh[i][j], 0)]

        # Solution Tested
        model.start = [(r, 1)]
        model.start = [(x[0], 1)]
        model.start = [(x[3], 1)]
        model.start = [(x[4], 1)]
        model.start = [(x[6], 1)]
        model.start = [(x[7], 1)]
        model.start = [(x[8], 1)]
        model.start = [(x[9], 1)]
        model.start = [(x[13], 1)]
        model.start = [(x[14], 1)]
        model.start = [(y[0], 1)]
        model.start = [(y[1], 1)]
        model.start = [(y[2], 1)]
        model.start = [(y[10], 1)]
        model.start = [(y[11], 1)]
        model.start = [(y[17], 1)]
        model.start = [(y[18], 1)]
        model.start = [(L_sub[0], 105)]
        model.start = [(L_sub[3], 105)]
        model.start = [(L_sub[4], 105)]
        model.start = [(L_sub[14], 105)]
        model.start = [(L_sub[17], 64)]
        model.start = [(L_sub[18], 41)]
        model.start = [(L_sub[57], 65)]
        model.start = [(L_sub[58], 40)]
        model.start = [(L_sub[71], 64)]
        model.start = [(L_sub[72], 64)]
        model.start = [(L_sub[75], 41)]
        model.start = [(L_sub[76], 41)]
        model.start = [(W_sub[0], 125)]
        model.start = [(W_sub[3], 59)]
        model.start = [(W_sub[4], 66)]
        model.start = [(W_sub[13], 59)]
        model.start = [(W_sub[14], 59)]
        model.start = [(W_sub[17], 66)]
        model.start = [(W_sub[18], 66)]
        model.start = [(W_sub[53], 59)]
        model.start = [(W_sub[54], 59)]
        model.start = [(W_sub[57], 59)]
        model.start = [(W_sub[58], 59)]
        model.start = [(W_sub[71], 29)]
        model.start = [(W_sub[72], 37)]
        model.start = [(W_sub[75], 31)]
        model.start = [(W_sub[76], 35)]
        model.start = [(delta[3][75], 1)]
        model.start = [(delta[10][76], 1)]
        model.start = [(delta[13][72], 1)]
        model.start = [(delta[16][58], 1)]
        model.start = [(delta[22][57], 1)]
        model.start = [(delta[23][71], 1)]

    # -----------------------------------------------------------#
    # Initialize the model variables with a predefined solution #
    # -----------------------------------------------------------#
    @staticmethod
    def test5arcs(model, x, z, L_sub, W_sub, delta, qh, qv, ii, jj, beta=[]):
        # Start with 0
        for j in jj:
            model.start = [(x[j], 0)]
            model.start = [(z[j], 0)]
            model.start = [(L_sub[j], 0)]
            model.start = [(W_sub[j], 0)]

        for i in ii:
            for j in jj:
                model.start = [(delta[i][j], 0)]
                model.start = [(qh[i][j], 0)]
                model.start = [(qv[i][j], 0)]

        # GUILLOTINE
        if len(beta) > 0:
            for j in jj:
                model.start = [(beta[j], 0)]

        # Solution to be tested
        model.start = [(x[0], 1.0)]
        model.start = [(x[1], 1.0)]
        model.start = [(x[2], 1.0)]
        model.start = [(x[3], 1.0)]
        model.start = [(x[4], 1.0)]
        model.start = [(L_sub[0], 105.0)]
        model.start = [(L_sub[1], 82.0)]
        model.start = [(L_sub[2], 23.0)]
        model.start = [(L_sub[3], 23.0)]
        model.start = [(L_sub[4], 82.0)]
        model.start = [(L_sub[6], 47.0)]
        model.start = [(L_sub[7], 35.0)]
        model.start = [(L_sub[8], 35.0)]
        model.start = [(L_sub[9], 47.0)]
        model.start = [(L_sub[11], 23.0)]
        model.start = [(L_sub[14], 23.0)]
        model.start = [(L_sub[17], 23.0)]
        model.start = [(L_sub[19], 23.0)]
        model.start = [(L_sub[20], 23.0)]
        model.start = [(L_sub[21], 26.0)]
        model.start = [(L_sub[22], 56.0)]
        model.start = [(L_sub[24], 82.0)]
        model.start = [(L_sub[25], 56.0)]
        model.start = [(W_sub[0], 125.0)]
        model.start = [(W_sub[1], 77.0)]
        model.start = [(W_sub[2], 47.0)]
        model.start = [(W_sub[3], 78.0)]
        model.start = [(W_sub[4], 48.0)]
        model.start = [(W_sub[5], 30.0)]
        model.start = [(W_sub[6], 77.0)]
        model.start = [(W_sub[7], 35.0)]
        model.start = [(W_sub[8], 42.0)]
        model.start = [(W_sub[10], 42.0)]
        model.start = [(W_sub[11], 47.0)]
        model.start = [(W_sub[13], 47.0)]
        model.start = [(W_sub[15], 47.0)]
        model.start = [(W_sub[16], 78.0)]
        model.start = [(W_sub[17], 78.0)]
        model.start = [(W_sub[21], 48.0)]
        model.start = [(W_sub[22], 48.0)]
        model.start = [(z[0], 1.0)]
        model.start = [(z[1], 1.0)]
        model.start = [(z[2], 1.0)]
        model.start = [(z[3], 1.0)]
        model.start = [(z[4], 1.0)]
        model.start = [(z[5], 1.0)]
        model.start = [(z[8], 1.0)]
        model.start = [(z[9], 1.0)]
        model.start = [(z[10], 1.0)]
        model.start = [(z[12], 1.0)]
        model.start = [(z[14], 1.0)]
        model.start = [(z[16], 1.0)]
        model.start = [(z[17], 1.0)]
        model.start = [(z[18], 1.0)]
        model.start = [(z[19], 1.0)]
        model.start = [(z[21], 1.0)]
        model.start = [(z[24], 1.0)]
        model.start = [(z[30], 1.0)]
        model.start = [(delta[5][7], 1.0)]
        model.start = [(delta[6][22], 1.0)]
        model.start = [(delta[7][17], 1.0)]
        model.start = [(delta[9][6], 1.0)]
        model.start = [(delta[14][21], 1.0)]
        model.start = [(delta[21][11], 1.0)]
        model.start = [(delta[35][8], 1.0)]
        model.start = [(qh[7][17], 1.0)]
        model.start = [(qh[14][21], 1.0)]
        model.start = [(qh[35][8], 1.0)]
        model.start = [(qv[5][7], 1.0)]
        model.start = [(qv[6][22], 1.0)]
        model.start = [(qv[9][6], 1.0)]
        model.start = [(qv[21][11], 1.0)]
        model.start = [(beta[20], 1.0)]
        model.start = [(beta[25], 1.0)]
