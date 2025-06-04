import numpy as np

def beta_bc_fcm(fcm28):
    return 1.8 / (fcm28 ** 0.7)

def beta_bc_t_t0(t, t0, t0_adj):
    return np.log(((30 / t0_adj) + 0.035) ** 2 * (t - t0) + 1)

def beta_dc_fcm(fcm28):
    return (412 / fcm28 ** 1.4)

def beta_dc_RH(RH, hn):
    return (1 - RH / 100) / (np.power(0.1 * hn / 100, 1/3)) 

def beta_dc_t0(t0):
    return 1 / (0.1 + t0**0.2)

def gamma_t0_adj(t0_adj):
    return 1 / (2.3 + 3.5 / np.sqrt(t0_adj))

def alpha_fcm(fcm28):
    return (35 / fcm28) ** 0.5

def beta_h(hn, fcm28):
    alpha_fcm_val = alpha_fcm(fcm28)
    return min(1.5 * hn + 250 * alpha_fcm_val, 1500 * alpha_fcm_val)

def beta_dc_t_t0(t, t0, beta_h_val, gamma_val):
    return ((t - t0) / (beta_h_val + (t - t0))) ** gamma_val

def alpha_sc(concrete_class):
    return {"CS": -1, "CN": 0, "CR": 1}.get(concrete_class, 0)

def t0_adj(t0_T, alpha_sc):
    return max(t0_T * ((9 / (2 + t0_T**1.2) + 1) ** alpha_sc), 0.5)

def t_T(temperature_intervals):
    return sum(dt * np.exp(13.65 - 4000 / (273 + T)) for dt, T in temperature_intervals)

def varphi_bc(t, t0, fcm28, t0_adj):
    return beta_bc_fcm(fcm28) * beta_bc_t_t0(t, t0, t0_adj)

def varphi_dc(t, t0, fcm28, RH, hn, t0_adj):
    beta_fcm = beta_dc_fcm(fcm28)
    beta_RH_val = beta_dc_RH(RH, hn)
    beta_t0 = beta_dc_t0(t0_adj)
    gamma_val = gamma_t0_adj(t0_adj)
    beta_h_val = beta_h(hn, fcm28)
    beta_t_t0 = beta_dc_t_t0(t, t0, beta_h_val, gamma_val)
    
    return beta_fcm * beta_RH_val * beta_t0 * beta_t_t0

def creep_coef(t, t0, fcm28, RH, hn, t0_T, concrete_class):
    """Calculates the creep coefficient based on time, initial time, concrete compressive strength, relative humidity, effective height, initial temperature, and concrete class.
    This function computes the creep coefficient using the coefficients defined for different concrete compressive strengths, relative humidity, and time.
    The creep coefficient is a measure of the time-dependent deformation of concrete under sustained load.
    It combines the effects of basic creep and drying creep, adjusted for the initial time and temperature.
    The function uses the concrete class to determine the adjustment factor for the initial time.
    The function returns the total creep coefficient as a float value.
    Uses EN1992-1:2025.

    Args:
        t (_type_): _description_
        t0 (_type_): _description_
        fcm28 (_type_): _description_
        RH (_type_): _description_
        hn (_type_): _description_
        t0_T (_type_): _description_
        concrete_class (_type_): _description_

    Returns:
        _type_: _description_
    """
    alpha_sc_val = alpha_sc(concrete_class)
    t0_adj_val = t0_adj(t0_T, alpha_sc_val)
    return varphi_bc(t, t0, fcm28, t0_adj_val) + varphi_dc(t, t0, fcm28, RH, hn, t0_adj_val)


if __name__ == "__main__":
    t = 365 * 50
    t0 = 3
    fck = 35
    fcm28 = fck + 8
    RH = 50
    hn = 100
    concrete_class = "CS"
    t0_T = t0
    varphi_val = creep_coef(t, t0, fcm28, RH, hn, t0_T, concrete_class)
    print(f"Varphi({t=}, {t0=}, {fck=}, {RH=}, {hn=}, {t0_T=}) = {varphi_val:.3f}")

    import csv
    import numpy as np
    from itertools import product
    from scipy.optimize import curve_fit

    list_hn = [100, 300, 500, 700, 1000]
    list_RH = [50, 65, 80,]
    list_t0 = [1, 3, 7, 28, 91, 365]
    list_class = ['CS', 'CN', 'CR']
    # list_fcm = [33, 43, 53, 63, 73]  # Added list of fcm values
    # list_fck = [25, 35, 45, 55, 65]  # Added list of fcm values
    # fck_ref = 35
    list_fcm = [28, 38, 48, 58, 68]  # Added list of fcm values
    list_fck = [20, 30, 40, 50, 60]  # Added list of fcm values
    fck_ref = 30
    fcm_ref = fck_ref + 8

    # combinations = list(product(list_class,list_fck, list_hn, list_RH))

    with open("creep_data.csv", mode="w", newline="") as file:
        writer = csv.writer(file)
        row = ["Concrete Class", "RH (%)", "t0 (dias)"] + [f"Hn {hni} (mm)" for hni in list_hn]
        writer.writerow(row)

        fcm = 35+8
        for class_conc, RHi, t0 in product(list_class, list_RH, list_t0):
            row = [class_conc, RHi, t0]
            row.extend( round(creep_coef(50*365, t0, fcm, RHi, hni, t0, class_conc), 3) for hni in list_hn)
            writer.writerow(row)

    print("CSV file 'creep_data.csv' has been created successfully!")

        # Open the CSV file for writing
    with open("creep_data-qwen.csv", mode="w", newline="") as file:
        writer = csv.writer(file)
        
        # Write the header row
        row = ["Concrete Class", "fcm (MPa)", "RH (%)", "t0 (days)"] + [f"Hn {hni} (mm)" for hni in list_hn]
        writer.writerow(row)
        
        # Generate all combinations of parameters
        combinations = list(product(list_class, list_fcm, list_RH, list_t0))
        
        # Calculate varphi for each combination and write to the CSV file
        for class_conc, fcm, RHi, t0 in combinations:
            row = [class_conc, fcm, RHi, t0]
            row.extend(round(creep_coef(50*365, t0, fcm, RHi, hni, t0, class_conc), 3) for hni in list_hn)
            writer.writerow(row)

    # Perform regression analysis for each Hn value and RH
    regression_results = {}

    # Extract phi values for each combination of hni and RH
    for hni in list_hn:
        for RHi in list_RH:
            phi_values = []
            fcm_values = []
            
            # Collect phi values for all fcm values at the current hni and RH
            all_phi_values = [[] for _ in range(len(list_fcm))]
            with open("creep_data-qwen.csv", mode="r") as file:
                reader = csv.reader(file)
                next(reader)  # Skip header
                
                for row in reader:
                    if float(row[2]) == RHi:  # Only consider rows where RH matches
                        fcm_index = list_fcm.index(float(row[1]))
                        all_phi_values[fcm_index].append(float(row[list_hn.index(hni) + 4]))
            
            # Compute average phi for each fcm
            avg_phi_values = [np.mean(phi_list) if len(phi_list) > 0 else None for phi_list in all_phi_values]
            
            # Ensure we have valid data for regression
            valid_indices = [i for i, val in enumerate(avg_phi_values) if val is not None]
            if not valid_indices:
                continue
            
            avg_phi_values = [avg_phi_values[i] for i in valid_indices]
            fck_values = [list_fck[i] for i in valid_indices]
            
            # Perform regression to find alpha
            log_phi_ratio = np.log(np.array(avg_phi_values) / avg_phi_values[valid_indices.index(list_fcm.index(fcm_ref))])
            values_35 = np.array([fck_ref for _ in fck_values])
            log_fcm_ratio = np.log(np.array(values_35 / fck_values))
            
            if len(log_phi_ratio) >= 2:  # Ensure enough data points for regression
                alpha, _ = np.polyfit(log_fcm_ratio, log_phi_ratio, 1)
                regression_results[(RHi, hni)] = alpha

    # Output regression results
    print("Regression results:")
    for (RHi, hni), alpha in regression_results.items():
        print(f"For Hn = {hni} mm and RH = {RHi}%, alpha = {alpha:.3f}")
    
    for RHi in list_RH:
        s = f"{RHi=}:    "
        for hni in list_hn:
            s += f"{regression_results[(RHi, hni)]:.3f}  "
        print(s)

    print("CSV file 'creep_data-qwen.csv' has been created successfully!")

    # Step 3: Write the calculated and predicted varphi values to a new CSV file
    with open("creep_data_with_predictions.csv", mode="w", newline="") as file:
        writer = csv.writer(file)
        
        # Write the header row
        row = ["Concrete Class", "fcm (MPa)", "RH (%)", "t0 (days)"]
        for hni in list_hn:
            row.extend([f"Calculated Hn {hni} (mm)", f"Predicted Hn {hni} (mm)"])
        writer.writerow(row)
        
        # Generate all combinations of parameters
        combinations = list(product(list_class, list_fcm, list_RH, list_t0))
        
        for class_conc, fcm, RHi, t0 in combinations:
            row = [class_conc, fcm, RHi, t0]
            
            for hni in list_hn:
                # Calculate the varphi value
                calculated_varphi = creep_coef(50*365, t0, fcm, RHi, hni, t0, class_conc)
                
                # Predict the varphi value using the regression formula
                alpha = regression_results.get((RHi, hni), None)
                if alpha is not None and fcm != fcm_ref:
                    base_varphi = creep_coef(50*365, t0, fcm_ref, RHi, hni, t0, class_conc)
                    predicted_varphi = base_varphi * (fck_ref / (fcm-8)) ** alpha
                else:
                    predicted_varphi = calculated_varphi  # If no alpha or fcm=35, use calculated value
                
                # Add calculated and predicted values to the row
                row.extend([round(calculated_varphi, 3), round(predicted_varphi, 3)])
            
            writer.writerow(row)

    print("CSV file 'creep_data_with_predictions.csv' has been created successfully!")