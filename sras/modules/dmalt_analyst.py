# パッケージの読み込み
import pandas as pd
import numpy as np
import math
import scipy.special # 第1種の不完全ガンマ関数

from scipy import optimize

class DMALTanalyst:
    # コンストラクタ
    def __init__(self, uploadfile):
        self.t = uploadfile.tData
        self.y = uploadfile.yData
        self.t_title = uploadfile.df.columns[0]
        self.y_title = uploadfile.df.columns[1]
        # 分布の設定
        self.dist = uploadfile.srmodel
        # 初期値の設定
        if self.dist in ["dmalt_gamma", "dmalt_wei"]:
            self.theta = [float(uploadfile.init_a), float(uploadfile.init_b), float(uploadfile.init_c)]
        else:
            self.theta = [float(uploadfile.init_a), float(uploadfile.init_b)]
        self.max_tPrediction = int(uploadfile.max_tPrediction)
        self.tPrediction = uploadfile.tPrediction
        # メトリクスの情報
        self.n_metrics = uploadfile.n_metrics
        self.metrics_info = uploadfile.metrics_info
        # メトリクスデータ
        self.metrics = self.getMetricsDataFromDF(uploadfile)  # 累積または差分値を格納
        self.z = self.getZ(self.metrics_info, self.metrics)   # 差分値に変換したメトリクス
        self.beta = self.getBeta(self.metrics_info)
        # 結果を格納するための辞書を初期化する
        self.result = {}
        # 最適化に成功したかどうか
        self.success = True

    def getMetricsDataFromDF(self, uploadfile):
        """ データフレームからメトリクスデータを取得して2次元リストとして返す """
        iter = 2
        metrics = []
        while iter < uploadfile.n_metrics + 2:
            met = uploadfile.df.iloc[:, iter].tolist()
            metrics.append(met)
            iter += 1

        return metrics

    def getZ(self, metrics_info, metrics):
        """ 累積値か差分値を判断して，差分値のZを返す """
        z = []
        iter = 0
        while iter < self.n_metrics:
            if metrics_info[iter]['acumulation'] == 'on':
                # 累積値なので差分値を作る
                j = 0
                while j < len(metrics[iter]):
                    if j == 0:
                        new_z = []
                        new_z.append(0)
                    else:
                        new_z.append(metrics[iter][j] - metrics[iter][j-1])
                    j += 1
                z.append(new_z)
            else:
                # 差分値なのでそのまま追加
                z.append(metrics[iter])
            iter += 1
        return z
    def getBeta(self, metrics_info):
        """ メトリクスの重みパラメータの初期値を得る """
        beta = []
        for met in metrics_info:
            beta.append(float(met['init']))
            # print(met['init'])
        return beta

    def M_dmalt(self, theta, beta, i):
        """
        DMALT モデルの平均値関数
            self.dist == 'dmalt_earlang' : s-shaped
                      == 'dmalt_ray'   : rayleigh
                      == 'dmalt_gamma' : gamma
                      == 'dmalt_wei'   : weibull
                          else         :  exponential
        """
        omega = theta[0]
        b = theta[1]
        if len(theta) == 3:
            c = theta[2]
        tt = self.B_i(beta, i)
        if self.dist == 'dmalt_earlang':
            return omega * (1.0 - (1 + b * tt) * math.exp(-b * tt))
        elif self.dist == 'dmalt_ray':
            return omega * (1 - math.exp(- tt * tt / (2.0 * b * b)))
        elif self.dist == 'dmalt_gamma':
            return omega * scipy.special.gammainc(c, b * tt)
        elif self.dist == 'dmalt_wei':
            return omega * (1 - math.exp(- b * tt**c))
        else:
            # print(omega, b, tt)
            return omega * (1.0 - math.exp(- b * tt))

    def B_i(self, beta, i):
        """ B_i,beta  """
        if i <= 0:
            return 0
        k = 1
        bi = 0.0
        while k <= i:
            bi += self.get_exp_Z_beta(beta, k) * (self.tPrediction[k] - self.tPrediction[k-1])
            k += 1
        return bi

    def get_exp_Z_beta(self, beta, k):
        """ exp(z_k^T * beta) を返す """
        sum = 0.0
        iter = 0
        while iter < self.n_metrics:
            sum += self.z[iter][k] * beta[iter]
            iter += 1
        return math.exp(sum)

    def M_nhpp(self, theta, t_dmalt):
        """ NHPP モデルの平均値関数 """
        if self.dist == "dmalt_earlang":
            return theta[0] * (1 - (1 + theta[1] * t_dmalt) * math.exp(- theta[1] * t_dmalt))
        elif self.dist == "dmalt_ray":
            return theta[0] * (1 - math.exp(- (t_dmalt ** 2.0) /  (2.0 * theta[1] ** 2.0)))
        elif self.dist == "dmalt_gamma":
            return theta[0] * scipy.special.gammainc(theta[2], theta[1] * t_dmalt)
        elif self.dist == "dmalt_wei":
            return theta[0] * (1 - math.exp(- theta[1] * t_dmalt**theta[2]))
        else:
            return theta[0] * (1 - math.exp(- theta[1] * t_dmalt))

    def LLF(self, t, y, z, theta, beta):
        """ 対数尤度関数 """
        n = max(t)
        k = 1
        sum = 0
        while k <= n:
            sum += (y[k] - y[k-1]) \
                * math.log(self.M_dmalt(theta, beta, k) - self.M_dmalt(theta, beta, k-1))
            k += 1
        sum += - self.M_dmalt(theta, beta, n)

        k = 1
        while k <= n:
            sum += - math.log(math.factorial(y[k]-y[k-1]))
            k += 1

        return sum

    def objective_function(self, params):
        """ 目的関数 """
        """ params は [omega, b, beta1, beta2, ...] """
        """ または [omega, b, c, beta1, beta2, ...] """
        if len(self.theta) == 3:
            theta = params[0:3]
            beta = params[3:]
        else:
            theta = params[0:2]
            beta = params[2:]
        llf = - self.LLF(self.t, self.y, self.z, theta, beta)
        return llf

    def AIC(self, llf):
        """ AIC """
        if self.dist in ["dmalt_gamma", "dmalt_wei"]:
            pi = 3 + self.n_metrics  # パラメータ数
        else:
            pi = 2 + self.n_metrics  # パラメータ数
        return (-2.0 * llf + 2.0 * pi)


    def BIC(self, llf):
        """ BIC """
        if self.dist in ["dmalt_gamma", "dmalt_wei"]:
            pi = 3 + self.n_metrics  # パラメータ数
        else:
            pi = 2 + self.n_metrics  # パラメータ数
        phi = (len(self.y) - 1) * (1 + self.n_metrics)
        return (-2.0 * llf + pi * math.log(phi))

    def MSE(self, y, ht):
        """  MSE """
        n = len(y) - 1
        k = 1
        mse = 0.0
        while k <= n:
            mse += (self.y[k] - ht[k]) ** 2.0
            k += 1
        return (mse / n)

    def AddDetedtecFaults(self, uploadfile):
        """ 各期の検出フォールト数をデータフレームに追加する """
        (row, col) = uploadfile.df.shape  # サイズを取り出す
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

    def AddIntensity(self, uploadfile):
        """ 強度関数をデータフレームに追加 """
        row = uploadfile.df.shape[0]  # サイズを取り出す
        intensity = [0] * row
        intensity[0] = np.nan
        intensity[1] = uploadfile.df.loc[1, "H(t)"]
        r = 2
        while r < row:
            intensity[r] = uploadfile.df.loc[r, "H(t)"] - uploadfile.df.loc[r-1, "H(t)"]
            r += 1
        uploadfile.df['h(t)'] = intensity


    def run(self, uploadfile):
        """
        パラメータ推定を実行する
        """

        # パラメータ初期値を平べったいリストとして生成する
        params = []
        for theta in self.theta:
            params.append(theta)
        for beta in self.beta:
            params.append(beta)

        # 最適化の実行
        try:
            res = optimize.fmin(self.objective_function, params)
        except ValueError:
            res = [-math.inf, -math.inf]
            self.success = False

        # 最適解のパラメータ
        omega_hat = res[0]
        b_hat = res[1]
        if self.dist in ["dmalt_gamma", "dmalt_wei"]:
            c_hat = res[2]
            theta_hat = [omega_hat, b_hat, c_hat]
            iter = 3
        else:
            theta_hat = [omega_hat, b_hat]
            iter = 2

        beta_hat = []
        for met in self.metrics_info:
            met['beta_hat'] = res[iter]
            beta_hat.append(res[iter])
            iter += 1

        # 評価尺度の取得
        llf = - self.objective_function(res)
        aic = self.AIC(llf)
        bic = self.BIC(llf)

        # 平均2乗誤差
        Ht4mse = [self.M_dmalt(theta_hat, beta_hat, i) for i in range(0,len(self.t))]
        mse = self.MSE(self.y, Ht4mse)

        # # 横軸を増やす作業
        # (row, col) = uploadfile.df.shape
        # x = uploadfile.df.iloc[row-1, 0] + 1

        # # 列数分の np.nan を準備する
        # # nan = [np.nan] * (col - 1)

        # while x <= self.max_x:
        #     r = [x]
        #     for i in range(1, col):
        #         r.append(np.nan)
        #     addRow = pd.DataFrame(r, index=uploadfile.df.columns).T
        #     uploadfile.df = uploadfile.df.append(addRow)
        #     x += 1
        # t4h = uploadfile.df.iloc[:, 0].tolist()



        # 平均値関数をデータフレームに追加
        Ht = [self.M_dmalt(theta_hat, beta_hat, i) for i in range(0,len(self.tPrediction))]
        uploadfile.df['H(t)'] = Ht

        # 各期の実測検出バグ数をデータフレームに追加
        self.AddDetedtecFaults(uploadfile)

        # 強度関数をデータフレームに追加
        self.AddIntensity(uploadfile)


        # print(Ht4mse)
        # for i in range(0,len(self.t)):
        #     result = self.M_dmalt(theta_hat, beta_hat, i)
        #     print(i, result)

        # result = self.LLF(self.t, self.y, self.z, self.theta, self.beta)
        # print(result)
        # params = []
        # for theta in self.theta:
        #     params.append(theta)
        # for beta in self.beta:
        #     params.append(beta)
        # print([self.theta, self.beta])
        # print(params)
        # result = self.objective_function(params)
        # print(result)

        self.result['a_hat'] = omega_hat
        self.result['b_hat'] = b_hat
        if self.dist in ["dmalt_gamma", "dmalt_wei"]:
            self.result['c_hat'] = c_hat
        for met in self.metrics_info:
            self.result[met['name']] = met['beta_hat']
        self.result['LLF'] = llf
        self.result['AIC'] = aic
        self.result['BIC'] = bic
        self.result['MSE'] = mse

        uploadfile.success = self.success

        # self.M_nhpp(self.theta, 1)
        # print(self.metrics_info)
        # print(self.beta)
        # print("-----------------")
        # print(self.metrics)
        # print(self.z)
        # print("-----------------")
        return self.result
