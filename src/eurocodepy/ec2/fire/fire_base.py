import math
import numpy as np
import pandas as pd

## Tables for tabulated data fire methods
def delta_a(eta_fi, gamma_s, fyk, as_req_prov):
    sig_s0 = np.array([20, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000, 1100, 1200])
    sig_kt = np.array([1.0, 0.999999, 0.9, 0.85, 0.8, 0.6, 0.35, 
                       0.1, 0.08, 0.06, 0.04, 0.02, 0.0])
    sig_s = eta_fi * fyk * as_req_prov / gamma_s
    k_s = sig_s / fyk
    temp = np.interp(k_s, np.flip(sig_kt), np.flip(sig_s0))
    valid = 345 <= temp <= 705
    return round(0.1 * (500 - temp), 0), temp, valid
    
wall_a40rei = np.array([
    [10, 10, 10],
    [10, 15, 20],
    [20, 25, 30],
    [25, 30, 35],
    [35, 40, 45],
    [40, 45, 50] ])

wall_h40rei = np.array([
    [100, 110, 120],
    [110, 120, 130],
    [120, 135, 140],
    [135, 150, 160],
    [155, 170, 180],
    [180, 200, 210] ])

wall_h40r = np.array([
    [100, 120, 130],
    [120, 155, 170],
    [140, 185, 210],
    [165, 210, 240],
    [200, 250, 280],
    [250, 305, 340] ])

wall_a40r = np.array([
    [10, 10, 10],
    [15, 20, 25],
    [20, 30, 35],
    [30, 40, 45],
    [45, 50, 45],
    [50, 55, 60] ])

wall_h25rei = np.array([
    [ 80,  90, 100],
    [ 90, 100, 110],
    [100, 110, 120],
    [120, 120, 130],
    [150, 150, 150],
    [170, 175, 175] ])

wall_h25r = np.array([
    [ 90, 100, 110],
    [110, 125, 140],
    [125, 155, 170],
    [140, 175, 200],
    [175, 215, 240],
    [200, 250, 280] ])

wall_a25rei = np.array([
    [10, 10, 10],
    [10, 10, 15],
    [10, 15, 20],
    [15, 20, 25],
    [20, 25, 30],
    [25, 30, 35] ])

wall_a25r = np.array([
    [10, 10, 10],
    [10, 15, 20],
    [15, 25, 30],
    [25, 35, 40],
    [30, 40, 45],
    [35, 45, 50] ])

beam_bsimp = np.array([
    [ 80, 120, 160, 200],
    [120, 160, 200, 300],
    [150, 200, 300, 400],
    [200, 240, 300, 500],
    [240, 300, 400, 600],
    [280, 350, 500, 700] ])

beam_bwsimp = np.array([
    [ 80],
    [100],
    [110],
    [120],
    [140],
    [160] ])

beam_asimp = np.array([
    [25, 20, 15, 15],
    [40, 35, 30, 25],
    [55, 45, 40, 35],
    [65, 60, 55, 50],
    [80, 70, 65, 60],
    [90, 80, 75, 70] ])

tables = [
  wall_a40rei,
  wall_h40rei,
  wall_h40r,
  wall_a40r,
  wall_h25rei,
  wall_h25r,
  wall_a25rei,
  wall_a25r,
  beam_bsimp,
  beam_bwsimp,
  beam_asimp
]

## Tables concrete and steel properties
stemp = np.array([20, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000, 1100, 1200])
sig_ks = np.array(['ksyt_hot', 'ksyt_cold', 'kspt_hot', 
                   'kspt_cold', 'kse', 'kest_hot', 'kest_cold'])

values_ks = np.array([
    [ 1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00],
    [ 1.00, 1.00, 1.00, 0.96, 1.00, 1.00, 1.00],
    [ 1.00, 1.00, 0.81, 0.92, 0.95, 0.90, 0.87],
    [ 1.00, 1.00, 0.61, 0.81, 0.90, 0.80, 0.72],
    [ 1.00, 0.94, 0.42, 0.63, 0.85, 0.70, 0.56],
    [ 0.78, 0.67, 0.36, 0.44, 0.60, 0.60, 0.40],
    [ 0.47, 0.40, 0.18, 0.26, 0.35, 0.31, 0.24],
    [ 0.23, 0.12, 0.07, 0.08, 0.10, 0.13, 0.08],
    [ 0.11, 0.11, 0.05, 0.06, 0.08, 0.09, 0.06],
    [ 0.06, 0.08, 0.04, 0.05, 0.06, 0.07, 0.05],
    [ 0.04, 0.05, 0.02, 0.03, 0.04, 0.04, 0.03],
    [ 0.02, 0.03, 0.01, 0.02, 0.02, 0.02, 0.02],
    [ 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00]
    ])

sig_kc = np.array(['kct_sil', 'kct_cal', 'kct_70', 'eps1t', 'epsu1t'])
values_kc = np.array([
    [ 1.00, 1.00, 1.00, 0.0025, 0.0200],
    [ 1.00, 1.00, 1.00, 0.0040, 0.0225],
    [ 0.95, 0.97, 0.75, 0.0055, 0.0250],
    [ 0.85, 0.91, 0.75, 0.0070, 0.0275],
    [ 0.75, 0.85, 0.75, 0.0100, 0.0300],
    [ 0.60, 0.74, 0.60, 0.0150, 0.0325],
    [ 0.45, 0.60, 0.45, 0.0250, 0.0350],
    [ 0.30, 0.43, 0.30, 0.0250, 0.0375],
    [ 0.15, 0.27, 0.15, 0.0250, 0.0400],
    [ 0.08, 0.15, 0.08, 0.0250, 0.0425],
    [ 0.04, 0.06, 0.04, 0.0250, 0.0450],
    [ 0.01, 0.02, 0.01, 0.0250, 0.0475],
    [ 0.00, 0.00, 0.00, math.nan, math.nan]
    ])

df_conc = pd.DataFrame(data=values_kc, index=stemp, columns=sig_kc)
df_steel = pd.DataFrame(data=values_ks, index=stemp, columns=sig_ks)
