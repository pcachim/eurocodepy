import numpy as np


def RH_eq(fcm28):
    return min(99 * (35 / fcm28) ** 0.1, 99)

def beta_RH(RH, RH_eq, variant=2):
    if RH >= 20 and RH <= RH_eq:
        return 1.55 * (1 - (RH / RH_eq) ** 3)
    elif RH > RH_eq and RH < 100:
        return 1.55 * (1 - (RH / RH_eq) ** 2)
    elif RH == 100:
        return 1.55 * (1 - (RH / RH_eq) ** 2) - 0.25
    else:
        raise ValueError("Invalid RH. Shoukd be > 20%.")

def beta_ds_t_ts(t, ts, hn):
    a = (t - ts) / (0.035 * hn**2 + (t - ts))
    if a < 0:
        return np.nan
    return np.sqrt(a)

def get_alpha_bs_ds(concrete_class):
    coefficients = {
        "CS": (800, 3),
        "CN": (700, 4),
        "CR": (600, 6)
    }
    return coefficients.get(concrete_class, (700, 4))

def epsilon_cbs_fcm(fcm28, alpha_bs):
    return alpha_bs * ((fcm28 / (60 + fcm28)) ** 2.5) * 1e-6

def beta_bs_t(t):
    return 1 -  np.exp(-0.2 *  np.sqrt(t))

def epsilon_cds_fcm(fcm28, alpha_ds):
    return (220 + 110 * alpha_ds) *  np.exp(-0.012 * fcm28) * 1e-6

def epsilon_cbs(t, fcm28, alpha_bs, alpha_NDP_b):
    return epsilon_cbs_fcm(fcm28, alpha_bs) * beta_bs_t(t) * alpha_NDP_b

def epsilon_cds(t, ts, fcm28, RH, hn, alpha_ds, alpha_NDP_d):
    RH_eq_val = RH_eq(fcm28)
    beta_RH_val = beta_RH(RH, RH_eq_val)
    beta_ds_val = beta_ds_t_ts(t, ts, hn)
    eps_cds_fcm_val = epsilon_cds_fcm(fcm28, alpha_ds)
    
    return eps_cds_fcm_val * beta_RH_val * beta_ds_val * alpha_NDP_d

def shrink_strain(t, ts, fcm28, RH, hn, concrete_class, alpha_NDP_b, alpha_NDP_d):
    """Calculates the total shrinkage and creep strain of concrete based on time, initial time, concrete compressive strength, relative humidity, effective height, concrete class, and coefficients for cement type.
    This function computes the total strain by combining the basic creep strain and drying shrinkage strain, adjusted for the initial time and temperature.
    The basic creep strain is calculated using the concrete compressive strength and the coefficients for the concrete class.
    The drying shrinkage strain is calculated using the relative humidity, effective height, and coefficients for the concrete class.
    The function returns the total strain as a float value. Uses EN1992-1:2025.

    Args:
        t (_type_): _description_
        ts (_type_): _description_
        fcm28 (_type_): _description_
        RH (_type_): _description_
        hn (_type_): _description_
        concrete_class (_type_): _description_
        alpha_NDP_b (_type_): _description_
        alpha_NDP_d (_type_): _description_

    Returns:
        _type_: _description_
    """
    alpha_bs, alpha_ds = get_alpha_bs_ds(concrete_class)
    return epsilon_cbs(t, fcm28, alpha_bs, alpha_NDP_b) + epsilon_cds(t, ts, fcm28, RH, hn, alpha_ds, alpha_NDP_d)


if __name__ == "__main__":
    # Example usage
    t = 365 * 50
    ts = 1
    fck = 80
    fcm28 = fck + 8
    RH = 80
    hn = 100
    concrete_class = "CS"
    alpha_NDP_b = 1
    alpha_NDP_d = 1
    
    for hnn in [100, 200, 500, 1000]:
        epsilon_cs_val = shrink_strain(t, ts, fcm28, RH, hnn, concrete_class, alpha_NDP_b, alpha_NDP_d) * 1000
        print(f"Epsilon_cs({t}, {ts}, {fcm28}, {RH}, {hnn}, {concrete_class}, {alpha_NDP_b}) = {epsilon_cs_val:.2f}")

    import matplotlib.pyplot as plt

    def generate_chart_data(fcm28, RH, hn, concrete_class, alpha_NDP_b, alpha_NDP_d):
        """
        Generates data for charts related to creep and shrinkage of concrete.

        Args:
            fcm28: Characteristic compressive strength of concrete at 28 days (MPa).
            RH: Relative humidity (%).
            hn: Notional size of the concrete member (mm).
            concrete_class: Class of concrete ('CS', 'CN', or 'CR').
            alpha_NDP_b: Coefficient depending on type of cement.
            alpha_NDP_d: Coefficient depending on type of cement.

        Returns:
            A dictionary containing the data for the charts.
        """

        t_values = np.linspace(0, 365 * 50, 500)  # Time in days, up to 50 years
        epsilon_cs_values = []

        for t in t_values:
            epsilon_cs_values.append(shrink_strain(t, 1, fcm28, RH, hn, concrete_class, alpha_NDP_b, alpha_NDP_d))

        return {
            "t_values": t_values,
            "epsilon_cs_values": epsilon_cs_values,
        }

    # Example usage:
    fcm28 = 30
    RH = 50
    hn = 100
    concrete_class = "CS"
    alpha_NDP_b = 1.0  # Example value
    alpha_NDP_d = 1.0  # Example value

    chart_data = generate_chart_data(fcm28, RH, hn, concrete_class, alpha_NDP_b, alpha_NDP_d)

    def draw_charts(chart_data):
        """
        Draws charts related to creep and shrinkage of concrete.

        Args:
            chart_data: A dictionary containing the data for the charts.
        """

        t_values = chart_data["t_values"]
        epsilon_cs_values = chart_data["epsilon_cs_values"]

        # Chart 1: Creep and shrinkage over time
        plt.figure(figsize=(10, 6))
        plt.plot(t_values, epsilon_cs_values)
        plt.xlabel("Time (days)")
        plt.ylabel("Creep and Shrinkage (x10^-6)")
        plt.title("Creep and Shrinkage Over Time")
        plt.grid(True)
    #    plt.show()

    # Example usage:
    draw_charts(chart_data)


    # Chart 2: Creep and shrinkage vs. fcm28
    fcm28_values = np.linspace(20, 50, 20)  # Range of fcm28 values
    epsilon_cs_values_fcm28 = []

    for fcm28 in fcm28_values:
        chart_data = generate_chart_data(fcm28, RH, hn, concrete_class, alpha_NDP_b, alpha_NDP_d)
        epsilon_cs_values_fcm28.append(chart_data["epsilon_cs_values"][-1])  # Use the last value for each fcm28

    plt.figure(figsize=(10, 6))
    plt.plot(fcm28_values, epsilon_cs_values_fcm28)
    plt.xlabel("fcm28 (MPa)")
    plt.ylabel("Creep and Shrinkage (x10^-6)")
    plt.title("Creep and Shrinkage vs. fcm28")
    plt.grid(True)
    # plt.show()

    # Chart 3: Creep and shrinkage vs. RH
    RH_values = np.linspace(20, 100, 20)  # Range of RH values
    epsilon_cs_values_RH = []

    for RH in RH_values:
        chart_data = generate_chart_data(fcm28, RH, hn, concrete_class, alpha_NDP_b, alpha_NDP_d)
        epsilon_cs_values_RH.append(chart_data["epsilon_cs_values"][-1])  # Use the last value for each RH

    plt.figure(figsize=(10, 6))
    plt.plot(RH_values, epsilon_cs_values_RH)
    plt.xlabel("RH (%)")
    plt.ylabel("Creep and Shrinkage (x10^-6)")
    plt.title("Creep and Shrinkage vs. RH")
    plt.grid(True)
    # plt.show()

    # Chart 4: Creep and shrinkage vs. hn
    hn_values = np.linspace(100, 1000, 20)  # Range of hn values
    RH_values = [50, 66, 80, 100]  # RH values to display

    plt.figure(figsize=(10, 6))

    for RH in RH_values:
        epsilon_cs_values_hn = []  # Initialize the list here
        for hn in hn_values:
            chart_data = generate_chart_data(fcm28, RH, hn, concrete_class, alpha_NDP_b, alpha_NDP_d)
            epsilon_cs_values_hn.append(chart_data["epsilon_cs_values"][-1])  # Use the last value for each hn
        plt.plot(hn_values, epsilon_cs_values_hn, label=f"RH = {RH}%")

    plt.figure(figsize=(10, 6))
    plt.plot(hn_values, epsilon_cs_values_hn)
    plt.xlabel("hn (mm)")
    plt.ylabel("Creep and Shrinkage (x10^-6)")
    plt.title("Creep and Shrinkage vs. hn")
    plt.grid(True)
    plt.show()

    def generate_table_data(fcm28, concrete_class, alpha_NDP_b, alpha_NDP_d):
        """
        Generates data for the table related to creep and shrinkage of concrete.

        Args:
            fcm28: Characteristic compressive strength of concrete at 28 days (MPa).
            concrete_class: Class of concrete ('CS', 'CN', or 'CR').
            alpha_NDP_b: Coefficient depending on type of cement.
            alpha_NDP_d: Coefficient depending on type of cement.

        Returns:
            A dictionary containing the data for the table.
        """

        RH_values = [50, 65, 80]
        t_values = [365]  # You specified t = 365 days
        hn_values = [100, 300, 500, 700, 1000]
        table_data = {}

        for RH in RH_values:
            table_data[RH] = {}
            for hn in hn_values:
                epsilon_cs_values = []
                for t in t_values:
                    epsilon_cs_values.append(shrink_strain(t, 1, fcm28, RH, hn, concrete_class, alpha_NDP_b, alpha_NDP_d)*1000.0)
                table_data[RH][hn] = epsilon_cs_values * 1000

        return table_data

    
    # Example usage:
    fcm28 = 30
    concrete_class = "CS"
    alpha_NDP_b = 1.0  # Example value
    alpha_NDP_d = 1.0  # Example value

    table_data = generate_table_data(fcm28, concrete_class, alpha_NDP_b, alpha_NDP_d)

    def print_table(table_data):
        """
        Prints the table related to creep and shrinkage of concrete.

        Args:
            table_data: A dictionary containing the data for the table.
        """

        RH_values = sorted(table_data.keys())
        hn_values = sorted(table_data[RH_values[0]].keys())

        # Print header row
        print("RH \\ hn\t", end="")
        for hn in hn_values:
            print(f"{hn}\t", end="")
        print()

        # Print data rows
        for RH in RH_values:
            print(f"{RH}\t", end="")
            for hn in hn_values:
                print(f"{table_data[RH][hn][0]:.2f}\t", end="")  # Assuming one t value
            print()

    # Example usage:
    print_table(table_data)

    import csv
    from itertools import product

    list_fck = [20, 30, 40, 50, 60]
    list_hn = [100, 300, 500, 700, 1000]
    list_RH = [50, 65, 80, 99, 100]
    list_class = ['CS', 'CN', 'CR']

    # combinations = list(product(list_class,list_fck, list_hn, list_RH))

    with open("shrinkage_data.csv", mode="w", newline="") as file:
        writer = csv.writer(file)
        row = ["Concrete Class", "RH (%)", "Fck28 (MPa)"] + [f"Hn {hni} (mm)" for hni in list_hn]
        writer.writerow(row)

        for class_conc, RHi, fck28 in product(list_class, list_RH, list_fck):
            row = [class_conc, RHi, fck28]
            row.extend( round(shrink_strain(50*365, 1, fck28+8, RHi, hni, class_conc, 1, 1) * 1000, 3) for hni in list_hn)
            writer.writerow(row)

    print("CSV file 'shrinkage_data.csv' has been created successfully!")