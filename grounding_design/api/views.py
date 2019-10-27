import json
import numpy as np
from scipy.optimize import minimize
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

a = []
resistivities = []


def get_resistivities_from_measurements(rod_depth, resistances):
    global a, resistivities

    a = np.mat(a)
    a = np.transpose(a)
    resistances = np.mat(resistances)
    resistivities = (4 * np.pi * np.multiply(a, resistances)) / \
                    (1 + (2 * a) / (np.sqrt(np.square(a) + 4 * rod_depth * rod_depth)) -
                     ((2 * a) / np.sqrt(4 * np.square(a) + 4 * rod_depth * rod_depth)))
    deviation = 100 * abs((resistivities - np.mean(resistivities, 1))) / np.mean(resistivities, 1)
    resistivities[deviation > 50] = np.nan
    resistivities = np.nanmean(resistivities, 1)
    resistivities = np.squeeze(np.asarray(resistivities))
    resistivities = resistivities.tolist()
    return resistivities


def stratification_function(x):
    global a, resistivities

    f = 0

    for i in range(len(a)):
        s = 0

        for n in range(1, 26):
            s = s + ((x[1] ** n) / np.sqrt(1 + ((2 * n * x[2]) / a[i]) ** 2) - (x[1] ** n) /
                     np.sqrt(4 + ((2 * n * x[2]) / a[i]) ** 2))

        f = f + (resistivities[i] - x[0] * (4 * s + 1)) ** 2

    return f


def get_two_layers_stratification():
    global a, resistivities
    a = np.squeeze(np.asarray(a))
    initial_guess = np.asarray([resistivities[0], -0.5, a[0]])

    minimum = minimize(stratification_function, initial_guess)['x']

    p1 = minimum[0]
    k = minimum[1]
    h = minimum[2]
    p2 = - p1 * (1 + k) / (k - 1)

    return [p1, k, h, p2]


def get_soil_resistivity(spacing, p1, k, h):
    f = np.zeros(len(spacing))

    for i in range(len(spacing)):
        s = 0

        for n in range(1, 26):
            s = s + ((k ** n) / np.sqrt(1 + ((2 * n * h) / spacing[i]) ** 2) - (k ** n) /
                     np.sqrt(4 + ((2 * n * h) / spacing[i]) ** 2))

        f[i] = p1 * (1 + 4 * s)

    return f


def get_km(signal, m, phi, alpha):
    if signal == '+':
        return alpha / np.sqrt(alpha ** 2 + (m + phi) ** 2)
    elif signal == '-':
        return alpha / np.sqrt(alpha ** 2 + (m - phi) ** 2)
    else:
        return alpha / np.sqrt(alpha ** 2 + m ** 2)


def get_cm(signal, m, phi, alpha):
    if signal == '+':
        return np.sqrt(1 + ((m + phi) / alpha) ** 2)
    elif signal == '-':
        return np.sqrt(1 + ((m - phi) / alpha) ** 2)
    else:
        return np.sqrt(1 + (m / alpha) ** 2)


def get_apparent_resistivity(width, length, h, p1, p2):
    phi = 0.5
    d0 = 1
    r = (width * length) / np.sqrt(width ** 2 + length ** 2)
    alpha = r / h
    beta = p2 / p1
    u = (beta - 1) / (beta + 1)
    s = 0

    for i in range(1, 26):
        s = s + (u ** i) * (get_km('+', i, phi, alpha) / get_cm('+', i, phi, alpha) +
                            (2 * get_km('', i, phi, alpha)) / get_cm('', i, phi, alpha) +
                            get_km('-', i, phi, alpha) / get_cm('-', i, phi, alpha))

    N = 1 + (s / (np.log((16 * r) / d0) + get_km('+', 0, phi, alpha) / get_cm('+', 0, phi, alpha)))
    
    return N * p1


def get_conductor_area(old_area):
    areas = [0.5, 0.75, 1, 1.5, 2.5, 4, 6, 10, 16, 25, 35, 50, 70, 95, 120, 150, 185, 240, 300]

    area = min([area for area in areas if area > old_area])

    if area < 35:
        area = 35

    return area


def get_correction_factor(pa, ps, h):
    if ps == 0:
        return 1
    else:
        K = (pa - ps) / (pa + ps)
        s = 0
        for n in range(1, 4):
            s = s + (K ** n) / np.sqrt(1 + (2 * n * (h / 0.08)) ** 2)
        return (1 / 0.96) * (2 * s + 1)


def get_kc(h, e, d, N):
    kcn = np.ones(2)
    kc = np.ones(2)
    x = np.array([0, 1])

    for i in range(len(kcn)):
        for j in range(2, N):
            kcn[i] = kcn[i] * (j * e + x[i]) / (j * e)
        kc[i] = (1 / (2 * np.pi)) * \
                (np.log((h ** 2 + x[i] ** 2) *
                        (h ** 2 + (e + x[i]) ** 2) / (h * d * (h ** 2 + e ** 2))) + 2 * np.log(kcn[i]))

    return kc[1] - kc[0]


def get_fence_potential(h, ea, eb, s_cu, na, nb, pa, i_grid, cable_length, rods_length):
    e = min(ea, eb)
    d = 2 * np.sqrt((s_cu * 10 ** (-6)) / np.pi)
    N = max(na, nb)
    kc = get_kc(h, e, d, N)
    N = np.sqrt(na * nb)
    ki = 0.656 + 0.172 * N
    return (pa * kc * ki * i_grid) / (cable_length + 1.15 * rods_length)


def get_Km(e, h_grid, d, kii, kh, N):
    return (1 / (2 * np.pi)) * (np.log((e ** 2) / (16 * h_grid * d) + ((e + 2 * h_grid) ** 2) / (8 * e * d) -
                                       h_grid / (4 * d)) + (kii / kh) * np.log(8 / (np.pi * (2 * N - 1))))


def get_grid_resistance(pa, total_length, width, length, h_grid):
    return pa * (1 / total_length + (1 / np.sqrt(20 * width * length) *
                                     (1 + 1 / (1 + h_grid * np.sqrt(20 / (width * length))))))


def get_number_error_message(variable):
    return 'The ' + variable + ' must be greater than zero.'


@csrf_exempt
def post(request):
    body = json.loads(request.body)

    global a, resistivities

    rod_depth = body['rod-depth']
    measurements = body['measurements']
    a = measurements['spacing']
    resistances = measurements['resistances']

    i_phase_ground = body['current-phase-ground']
    i_grid = body['current-grid']
    t_defect = body['defect-duration']
    width = body['grid-width']
    length = body['grid-length']
    ea = body['ea']
    eb = body['eb']
    h_grid = body['grid-height']
    h_rod = body['rod-height']

    p_gravel = body['gravel-resistivity']
    h_gravel = body['gravel-height']

    resistivities = get_resistivities_from_measurements(rod_depth, resistances)
    [p1, k, h, p2] = get_two_layers_stratification()
    a_curve = np.linspace(0, a[-1], num=100)
    resistivities_curve = get_soil_resistivity(a_curve, p1, k, h)
    a_curve = a_curve.tolist()
    resistivities_curve = resistivities_curve.tolist()
    # Step 1: Compute the apparent resistivity seen by the grid.
    pa = get_apparent_resistivity(width, length, h, p1, p2)
    # Step 2: Compute the gauge of the conductors forming the earth grid.
    i_defect = 0.6 * i_phase_ground
    theta_a = 30
    s_cu = (i_defect / 226.53) * \
           (1 / np.sqrt(((1 / t_defect) * np.log(((450 - theta_a) / (234 + theta_a)) + 1))))
    s_cu = get_conductor_area(s_cu)
    # Step 3: Compute the connecting cable gauge.
    s_connect = (i_phase_ground / 226.53) * \
                (1 / np.sqrt(((1 / t_defect) * np.log(((250 - theta_a) / (234 + theta_a)) + 1))))
    s_connect = get_conductor_area(s_connect)
    # Step 4: Compute the values of the maximum permissible potentials.
    cs = get_correction_factor(pa, p_gravel, h_gravel)
    if p_gravel == 0:
        ps = p1
    else:
        ps = p_gravel
    v_touch_max = (1000 + 1.5 * cs * ps) * (0.116 / np.sqrt(t_defect))
    v_step_max = (1000 + 6 * cs * ps) * (0.116 / np.sqrt(t_defect))
    # Step 5: Initial design for the grid.
    na = round(length / ea + 1)
    nb = round(width / eb + 1)
    ea = length / (na - 1)
    eb = width / (nb - 1)
    l_rods = 0
    n_rods = 0
    cable_length = na * width + nb * length
    total_length = cable_length
    # Step 6: Compute the grid's resistance
    r_grid_max = 10
    r_grid = get_grid_resistance(pa, total_length, width, length, h_grid)
    v_touch_grid = r_grid * i_grid
    if v_touch_grid < v_touch_max and r_grid < r_grid_max:
        N = max(na, nb)
        ki = 0.656 + 0.172 * N
        e = min(ea, eb)
        kp = (1 / np.pi) * (1 / (2 * h_grid) + (1 / (e + h_grid)) + (1 / e) * (1 - (0.5 ** (N - 2))))
        v_step_grid = (pa * kp * ki * i_grid) / (cable_length + 1.15 * l_rods)
        v_touch_fence = get_fence_potential(h_grid, ea, eb, s_cu, na, nb, pa, i_grid, cable_length, l_rods)
        if v_touch_grid < v_touch_max and v_step_grid < v_step_max and v_touch_fence < v_touch_max and r_grid < \
                r_grid_max:
            is_grid_safe = True
        else:
            is_grid_safe = False

        return JsonResponse({
            'is-grid-safe': is_grid_safe,
            'number-of-conductors-x-axis': na,
            'conductor-spacing-x-axis': ea,
            'number-of-conductors-y-axis': nb,
            'conductor-spacing-y-axis': eb,
            'grid-conductors-gauge': s_cu,
            'connection-cable-gauge': s_connect,
            'total-length': total_length,
            'number-of-rods': n_rods,
            'maximum-touch-voltage': v_touch_max,
            'maximum-step-voltage': v_step_max,
            'grid-touch-voltage': v_touch_grid,
            'grid-step-voltage': v_step_grid,
            'fence-touch-voltage': v_touch_fence,
            'grid-resistance': r_grid,
            'spacing-curve-data': a_curve,
            'resistivity-curve-data': resistivities_curve,
            'first-layer-resistivity': p1,
            'first-layer-depth': h,
            'second-layer-resistivity': p2,
            'resistivities': resistivities,
            'spacing': a.tolist()
        })
    else:
        # Step 7: Compute the grid potential during the fault.
        kh = np.sqrt(1 + h_grid)
        N = np.sqrt(na * nb)
        kii = 1 / ((2 * N) ** (2 / N))
        d = 2 * np.sqrt((s_cu * 10 ** (-6)) / np.pi)
        e = max(ea, eb)
        km = get_Km(e, h_grid, d, kii, kh, N)
        ki = 0.656 + 0.172 * N
        v_touch_grid = (pa * km * ki * i_grid) / total_length
        if v_touch_grid < v_touch_max and r_grid < r_grid_max:
            N = max(na, nb)
            ki = 0.656 + 0.172 * N
            e = min(ea, eb)
            kp = (1 / np.pi) * (1 / (2 * h_grid) + (1 / (e + h_grid)) + (1 / e) * (1 - (0.5 ** (N - 2))))
            v_step_grid = (pa * kp * ki * i_grid) / (cable_length + 1.15 * l_rods)
            v_touch_fence = get_fence_potential(h_grid, ea, eb, s_cu, na, nb, pa, i_grid, cable_length, l_rods)
            if v_touch_grid < v_touch_max and v_step_grid < v_step_max and v_touch_fence < v_touch_max and r_grid < \
                    r_grid_max:
                is_grid_safe = True
            else:
                is_grid_safe = False

            return JsonResponse({
                'is-grid-safe': is_grid_safe,
                'number-of-conductors-x-axis': na,
                'conductor-spacing-x-axis': ea,
                'number-of-conductors-y-axis': nb,
                'conductor-spacing-y-axis': eb,
                'grid-conductors-gauge': s_cu,
                'connection-cable-gauge': s_connect,
                'total-length': total_length,
                'number-of-rods': n_rods,
                'maximum-touch-voltage': v_touch_max,
                'maximum-step-voltage': v_step_max,
                'grid-touch-voltage': v_touch_grid,
                'grid-step-voltage': v_step_grid,
                'fence-touch-voltage': v_touch_fence,
                'grid-resistance': r_grid,
                'spacing-curve-data': a_curve,
                'resistivity-curve-data': resistivities_curve,
                'first-layer-resistivity': p1,
                'first-layer-depth': h,
                'second-layer-resistivity': p2,
                'resistivities': resistivities,
                'spacing': a.tolist()
            })
        else:
            # Step 8: Estimation of minimum conductor length
            minimum_length = i_grid * pa * ki * km / v_touch_max
            if total_length < minimum_length:
                # Step 9: Change the grid design
                n_rods = np.ceil((minimum_length - cable_length) / h_rod)
                l_rods = h_rod * n_rods
                total_length = cable_length + l_rods
                # Step 10: Compute the grid's potential.
                kii = 1
                km = get_Km(e, h_grid, d, kii, kh, N)
                r_grid = get_grid_resistance(pa, total_length, width, length, h_grid)
                v_touch_grid = (pa * km * ki * i_grid) / (cable_length + 1.15 * l_rods)
    # Step 11: Compute the step potential in the periphery of the mesh.
    N = max(na, nb)
    ki = 0.656 + 0.172 * N
    e = min(ea, eb)
    kp = (1 / np.pi) * (1 / (2 * h_grid) + (1 / (e + h_grid)) + (1 / e) * (1 - (0.5 ** (N - 2))))
    v_step_grid = (pa * kp * ki * i_grid) / (cable_length + 1.15 * l_rods)
    # Step 12: Compute the touch potential in the metal fence.
    v_touch_fence = get_fence_potential(h_grid, ea, eb, s_cu, na, nb, pa, i_grid, cable_length, l_rods)

    if v_touch_grid < v_touch_max and v_step_grid < v_step_max and v_touch_fence < v_touch_max and r_grid < r_grid_max:
        is_grid_safe = True
    else:
        is_grid_safe = False

    return JsonResponse({
        'is-grid-safe': is_grid_safe,
        'number-of-conductors-x-axis': na,
        'conductor-spacing-x-axis': ea,
        'number-of-conductors-y-axis': nb,
        'conductor-spacing-y-axis': eb,
        'grid-conductors-gauge': s_cu,
        'connection-cable-gauge': s_connect,
        'total-length': total_length,
        'number-of-rods': n_rods,
        'maximum-touch-voltage': v_touch_max,
        'maximum-step-voltage': v_step_max,
        'grid-touch-voltage': v_touch_grid,
        'grid-step-voltage': v_step_grid,
        'fence-touch-voltage': v_touch_fence,
        'grid-resistance': r_grid,
        'spacing-curve-data': a_curve,
        'resistivity-curve-data': resistivities_curve,
        'first-layer-resistivity': p1,
        'first-layer-depth': h,
        'second-layer-resistivity': p2,
        'resistivities': resistivities,
        'spacing': a.tolist()
    })
