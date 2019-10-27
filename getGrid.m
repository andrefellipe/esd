function [result, na, ea, nb, eb, Scu, Sconnect, lTotal, nRods, ...
    vTouchMax, vStepMax, vTouchGrid, vStepGrid, vTouchFence, rGrid, ...
    aCurve, resistivitiesCurve, p1, h, p2, resistivities] = ...
    getGrid(spacing, resistances, rodDepth, iPhaseGround, iGrid, ...
    tDeffect, width, length, pGravel, hGravel, thetaMcond, thetaMconn, ...
    ea, eb, hGrid, hRod)

nRods = 0; vStepGrid = 0; thetaA = 30; setA(spacing);
resistivities = getResistivitiesFromMeasurements(rodDepth, resistances);
[p1, k, h, p2] = getTwoLayersStratification;
aCurve = linspace(0, spacing(end));
resistivitiesCurve = getSoilResistivity(aCurve, p1, k, h);
% Step 1: Compute the apparent resistivity seen by the grid.
pa = getApparentResistivity(width, length, h, p1, p2);
% Step 2: Compute the gauge of the conductors forming the earth grid.
iDeffect = 0.6 * iPhaseGround;
Scu = (iDeffect / 226.53) * (1 / sqrt(((1 / tDeffect) * ...
    log(((thetaMcond - thetaA) / (234 + thetaA)) + 1))));
Scu = getConductorArea(Scu);
% Step 3: Compute the connecting cable gauge.
Sconnect = (iPhaseGround / 226.53) * (1 / sqrt(((1 / tDeffect) * ...
    log(((thetaMconn - thetaA) / (234 + thetaA)) + 1))));
Sconnect = getConductorArea(Sconnect);
% Step 4: Compute the values of the maximum permissible potentials.
cs = getCorrectionFactor(pa, pGravel, hGravel);
if pGravel == 0
    ps = p1;
else
    ps = pGravel;
end
vTouchMax = (1000 + 1.5 * cs * ps) * (0.116 / sqrt(tDeffect));
vStepMax = (1000 + 6 * cs * ps) * (0.116 / sqrt(tDeffect));
% Step 5: Initial design for the grid.
na = round(length / ea + 1);
nb = round(width / eb + 1);
ea = length / (na - 1);
eb = width / (nb - 1);
lCable = na * width + nb * length;
lTotal = lCable;
% Step 6: Compute the grid's resistance.
rGridMax = 10;
rGrid = pa * (1 / lTotal + (1 / sqrt(20 * width * length) * ...
    (1 + 1 / (1 + hGrid * sqrt(20 / (width * length))))));
vTouchGrid = rGrid * iGrid;
if vTouchGrid < vTouchMax && rGrid < rGridMax
    result = 'The grid meets all safety criteria.\n';
    vTouchFence = getFencePotential(hGrid, ea, eb, Scu, na, nb, pa, iGrid, ...
    lCable, 0);
    return
else
    % Step 7: Compute the grid potential during the fault.
    Kh = sqrt(1 + hGrid);
    N = sqrt(na * nb);
    Kii = 1 / ((2*N)^(2/N));
    d = 2 * sqrt((Scu * 10^(-6)) / pi);
    e = max(ea, eb);
    Km = (1 / (2 * pi)) * (log((e^2) / (16 * hGrid * d) + ...
        ((e + 2 * hGrid)^2) / (8 * e * d) - hGrid / (4 * d)) + ...
        (Kii / Kh) * log(8 / (pi * (2 * N - 1))));
    Ki = 0.656 + 0.172 * N;
    vTouchGrid = (pa * Km * Ki * iGrid) / lTotal;
    if vTouchGrid < vTouchMax && rGrid < rGridMax
        result = 'The grid meets all safety criteria.\n';
        vTouchFence = getFencePotential(hGrid, ea, eb, Scu, na, nb, pa, ...
            iGrid, lCable, 0);
        return
    else
        % Step 8: Estimation of minimum conductor length.
        lMin = iGrid * pa * Ki * Km / vTouchMax;
        if lTotal < lMin
            % Step 9: Change the grid design.
            nRods = ceil((lMin - lCable) / hRod);
            lRods = hRod * nRods;
            lTotal = lCable + lRods;
            % Step 10: Compute the grid's potential.
            Kii = 1;
            Km = (1 / (2 * pi)) * (log((e^2) / (16 * hGrid * d) + ...
                ((e + 2 * hGrid)^2) / (8 * e * d) - hGrid / (4 * d)) + ...
                (Kii / Kh) * log(8 / (pi * (2 * N - 1))));
            rGrid = pa * (1 / lTotal + (1 / sqrt(20 * width * length) * ...
                (1 + 1 / (1 + hGrid * sqrt(20 / (width * length))))));
            vTouchGrid = (pa * Km * Ki * iGrid) / (lCable + 1.15 * lRods);
        end
    end
end
% Step 11: Compute the step potential in the periphery of the mesh.
N = max(na, nb);
Ki = 0.656 + 0.172 * N;
e = min(ea, eb);
Kp = (1 / pi) * (1 / (2 * hGrid) + (1 / (e + hGrid)) + (1 / e) * ...
    (1 - (0.5 ^ (N - 2))));
vStepGrid = (pa * Kp * Ki * iGrid) / (lCable + 1.15 * lRods);
% Step 12: Compute the touch potential in the metal fence.
vTouchFence = getFencePotential(hGrid, ea, eb, Scu, na, nb, pa, ...
            iGrid, lCable, lRods);
if vTouchGrid < vTouchMax && vStepGrid < vStepMax && vTouchFence < ...
        vTouchMax && rGrid < rGridMax
    result = 'The grid meets all safety criteria.\n';
else
    result = 'The grid does not meet the safety criteria. Change the design or treat the soil.\n';
end

end

function area = getConductorArea(oldArea)

areas = [0.5 0.75 1 1.5 2.5 4 6 10 16 25 35 50 70 95 120 150 185 240 300];

area = min(areas(areas > oldArea));

if area < 35
    area = 35;
end

end

function vTouchFence = getFencePotential(h, ea, eb, Scu, na, nb, pa, iGrid, ...
    lCable, lRods)

e = min(ea, eb);
d = 2 * sqrt((Scu * 10^(-6)) / pi);
N = max(na, nb);
Kc = getKc(h, e, d, N);
N = sqrt(na * nb);
Ki = 0.656 + 0.172 * N;
vTouchFence = (pa * Kc * Ki * iGrid) / (lCable + 1.15 * lRods);

end

function Kc = getKc(h, e, d, N)

Kcn = ones(1, 2);
Kc = ones(1, 2);
x = [0 1];
da = length(Kcn);

for i = 1:length(Kcn)
    for j = 2:(N - 1)
        Kcn(i) = Kcn(i) * (j * e + x(i))/(j * e);
    end
    Kc(i) = (1/(2 * pi)) * (log((h^2 + x(i)^2)*(h^2 + (e + x(i))^2) / ...
    (h * d * (h^2 + e^2))) + 2 * log(Kcn(i)));
end

Kc = Kc(2) - Kc(1);

end

function cs = getCorrectionFactor(pa, ps, h)

if ps == 0
    cs = 1;
else
    K = (pa - ps) / (pa + ps);
    sum = 0;
    for n = 1:3
        sum = sum + (K ^ n) / sqrt(1 + (2 * n * (h / 0.08)) ^ 2);
    end
    cs = (1 / 0.96) * (2 * sum + 1);
end

end

function pa = getApparentResistivity(width, length, h, p1, p2)

phi = 0.5;
d0 = 1;
r = (width * length) / sqrt(width ^ 2 + length ^ 2);
alpha = r / h;
beta = p2 / p1;
u = (beta - 1) / (beta + 1);
sum = 0;

for i = 1:25
    sum = sum + (u ^ i) * (getKm('+', i, phi, alpha) / ...
        getCm('+', i, phi, alpha) + (2 * getKm('', i, phi, alpha)) / ...
        getCm('', i, phi, alpha) + getKm('-', i, phi, alpha) / ...
        getCm('-', i, phi, alpha));
end

N = 1 + (sum / (log((16 * r) / d0) + getKm('+', 0, phi, alpha) / ...
    getCm('+', 0, phi, alpha)));

pa = N * p1;

end

function cm = getCm(signal, m, phi, alpha)

    if isequal(signal, '+')
        cm = sqrt(1 + ((m + phi) / alpha) ^ 2);
    elseif isequal(signal, '-')
        cm = sqrt(1 + ((m - phi) / alpha) ^ 2);
    else
        cm = sqrt(1 + (m / alpha) ^ 2);
    end

end

function km = getKm(signal, m, phi, alpha)

    if isequal(signal, '+')
        km = alpha / sqrt(alpha ^ 2 + (m + phi) ^ 2);
    elseif isequal(signal, '-')
        km = alpha / sqrt(alpha ^ 2 + (m - phi) ^ 2);
    else
        km = alpha / sqrt(alpha ^ 2 + m ^ 2);
    end

end

function resistivities = getResistivitiesFromMeasurements(rodDepth, resistances)

a = getA;
resistivities = (4 * pi .* a .* resistances) ./ (1 + (2 .* a)./...
    (sqrt(a.^2 + 4 * rodDepth^2)) - ((2 .* a)./sqrt(4 .* a.^2 + ...
    4 * rodDepth^2)));
deviation = 100 * abs((resistivities - mean(resistivities, 2))) ./ ...
    mean(resistivities, 2);
resistivities(deviation > 50) = NaN;
resistivities = mean(resistivities, 2, 'omitnan');
setResistivities(resistivities);

end

function f = getSoilResistivity(a, p1, k, h)

f = zeros(1, length(a));

for i = 1:length(a)
    
    sum = 0;
    
    for n = 1:25
        sum = sum + (k ^ n) / sqrt(1 + ((2 * n * h) / a(i)) ^ 2)...
            - (k ^ n) / sqrt(4 + ((2 * n * h) / a(i)) ^ 2);
    end
    
    f(i) = p1 * (1 + 4 * sum);
end

end

function [p1, k, h, p2] = getTwoLayersStratification

a = getA;
resistivities = getResistivities;

initialGuess = [resistivities(1), -0.5, a(1)];

minimum = fminsearch(@stratificationFunction, initialGuess);
% opts = optimoptions('fminunc','Algorithm','quasi-newton');
% minimum = fminunc(@stratificationFunction, initialGuess, opts);

p1 = minimum(1);
k = minimum(2);
h = minimum(3);
p2 = - p1 * (1 + k) / (k - 1);

end