# パッケージの読み込み
import pandas as pd
import numpy as np
import math
import scipy.special # 第1種の不完全ガンマ関数

from scipy import optimize

class NHPPanalyst:
    # コンストラクタ
    def __init__(self, uploadfile):
        self.t = uploadfile.tData
        self.y = uploadfile.yData
        self.t_title = uploadfile.df.columns[0]
        self.y_title = uploadfile.df.columns[1]
        # 分布の設定
        self.dist = uploadfile.srmodel
        # 初期値の設定
        if self.dist in ["nhpp_gamma", "nhpp_wei"]:
            self.theta = [uploadfile.init_a, uploadfile.init_b, uploadfile.init_c]
        else:
            self.theta = [uploadfile.init_a, uploadfile.init_b]
        self.max_tPrediction = int(uploadfile.max_tPrediction)
        self.result = {}
        # 最適化に成功したかどうか
        self.success = True



    def F(self, da, b, c):
        """
        分布関数の値を返す
            self.dist == 'nhpp_earlang' : s-shaped
                      == 'nhpp_ray'   : rayleigh
                      == 'nhpp_gamma' : gamma
                      == 'nhpp_wei'   : weibull
                          else        :  exponential
        """
        if self.dist == 'nhpp_earlang':
            ft = 1 - (1 + b * da) * math.exp(-b * da)
        elif self.dist == 'nhpp_ray':
            ft = 1 - math.exp(- (da ** 2.0) / (2.0 * b ** 2.0))
        elif self.dist == 'nhpp_gamma':
            ft = scipy.special.gammainc(c, b * da)
        elif self.dist == 'nhpp_wei':
            ft = 1 - math.exp(- b * da**c)
        else:
            ft = 1 - math.exp(- b * da)
        return(ft)

    def h(self, ta, omega, b, c):
        """
        強度関数の値を返す
            self.dist == 'nhpp_earlang' : s-shaped
                      == 'nhpp_ray'   : rayleigh
                      == 'nhpp_gamma' : gamma
                      == 'nhpp_wei'   : weibull
                          else        :  exponential
        """
        if self.dist == 'nhpp_earlang':
            ht = omega * b * b * ta * math.exp(-b * ta)
        elif self.dist == 'nhpp_ray':
            ht = omega * ta / b / b * math.exp(- (ta * ta) / (2 * b * b))
        elif self.dist == 'nhpp_gamma':
            ht = omega * (b**c * ta**(c-1.0) * np.exp(-b*ta)) / math.gamma(c)
        elif self.dist == 'nhpp_wei':
            ht = omega * b * ta**(c-1) * math.exp(-b * ta**c)
        else:
            ht = omega * b * math.exp(- b * ta)
        return(ht)

    def Lambda(self, ta, omega, b, c):
        """平均値関数"""
        ft = self.F(ta, b, c)
        return (omega * ft)

    def LLF(self, t, y, omega, b, c):
        """対数尤度関数"""
        n = max(t)
        k = 1
        sum = 0
        while k <= n:
            sum += (y[k] - y[k-1]) \
                    * math.log(self.Lambda(t[k], omega, b, c) - self.Lambda(t[k-1], omega, b, c))
            k += 1
        sum += - self.Lambda(t[n], omega, b, c)

        k = 1
        while k <= n:
            sum += -math.log(math.factorial(y[k]-y[k-1]))
            k += 1
        return(sum)

    def objective_function(self, theta):
        """目的関数"""
        omega = theta[0]
        b = theta[1]
        if len(theta) == 3:
            c = theta[2]
        else:
            c = 1.0
        llf = - self.LLF(self.t, self.y, omega, b, c)
        return(llf)

    def AIC(self, llf):
        """AIC"""
        if self.dist in ["nhpp_gamma", "nhpp_wei"]:
            pi = 3
        else:
            pi = 2
        return(-2.0 * llf + 2 * pi)

    def BIC(self, llf):
        """BIC"""
        if self.dist in ["nhpp_gamma", "nhpp_wei"]:
            pi = 3
        else:
            pi = 2
        phi = len(self.y) - 1
        return(-2.0 * llf + pi * math.log(phi))

    def MSE(self, y, ht):
        """MSE"""
        n = len(y)-1
        k = 1
        mse = 0.0
        while k <= n:
            mse += (self.y[k] - ht[k]) ** 2.0
            k += 1
        return(mse / n)

    def AddDetedtecFaults(self, uploadfile):
        """ 各期の検出フォールト数をデータフレームに追加する """
        (row,col) = uploadfile.df.shape # サイズを取り出す
        len_y = len(self.y)
        faults = [0] * row
        r = 1
        while r < row:
            if r < len_y:
                faults[r] = self.y[r] - self.y[r-1]
            else:
                faults[r] = np.nan
            r += 1
        uploadfile.df['Delta y'] = faults

    def run(self, uploadfile):
        """
        パラメータ推定を実行する
        """
        # 最適化の実行
        try:
            res = optimize.fmin(self.objective_function, self.theta)
        except ValueError:
            res = [-math.inf, -math.inf]
            self.success = False


        # 最適解のパラメータ
        omega_hat = res[0]
        b_hat = res[1]
        if len(res) == 3:
            c_hat = res[2]
        else:
            c_hat = 1.0

        # 評価尺度の取得
        llf = - self.objective_function([omega_hat, b_hat, c_hat])
        aic = self.AIC(llf)
        bic = self.BIC(llf)

        # 平均2乗誤差
        Ht4mse = [self.Lambda(v, omega_hat, b_hat, c_hat) for v in self.t]
        mse = self.MSE(self.y, Ht4mse)

        tPrediction = uploadfile.tPrediction

        # 平均値関数をデータフレームに追加
        Ht = [self.Lambda(v, omega_hat, b_hat, c_hat) for v in tPrediction]
        uploadfile.df['H(t)'] = Ht

        # 各期の実測検出バグ数をデータフレームに追加
        self.AddDetedtecFaults(uploadfile)

        # 強度関数をデータフレームに追加
        ht = [self.h(v, omega_hat, b_hat, c_hat) for v in tPrediction]
        uploadfile.df['h(t)'] = ht

        self.result['a_hat'] = omega_hat
        self.result['b_hat'] = b_hat
        if len(res) == 3:
            self.result['c_hat'] = c_hat
        self.result['LLF'] = llf
        self.result['AIC'] = aic
        self.result['BIC'] = bic
        self.result['MSE'] = mse

        uploadfile.success = self.success

        return self.result
