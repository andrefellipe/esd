clear; clc;

spacing = [1 2 4 6 8 16 32];
resistances = [  82.7 ;
                 44.2 ;
                 16.1 ;
                  7.7 ;
                 4.69 ;
                 1.88 ;
                0.905 ];
% spacing = [1 2 4 8];
% resistances = [  50 18.5 15 ;
%                  7 10 6 ;
%                  2 3 1.6 ;
%                  1 0.4 11];
rodDepth = 0.5;
iPhaseGround = 3000;
iGrid = 1200;
tDeffect = 0.6;
width = 50;
length = 40;
pGravel = 3000;
hGravel = 0.2;
thetaMcond = 450;
thetaMconn = 250;
ea = 3;
eb = 3;
hGrid = 0.6;
hRod = 3;

[result, na, ea, nb, eb, Scu, Sconnect, lTotal, nRods, vTouchMax, ...
    vStepMax, vTouchGrid, vStepGrid, vTouchFence, rGrid, aCurve, ...
    resistivitiesCurve, p1, h, p2, resistivities] = ...
    getGrid(spacing, resistances, rodDepth, iPhaseGround, iGrid, ...
    tDeffect, width, length, pGravel, hGravel, thetaMcond, thetaMconn, ...
    ea, eb, hGrid, hRod);

fprintf(result);
fprintf('Number of cables in the x-axis: %.f\n', na);
fprintf('Spacing in the x-axis (m): %.2f\n', ea);
fprintf('Number of cables in the y-axis: %.f\n', nb);
fprintf('Spacing in the y-axis (m): %.2f\n', eb);
fprintf('Conductors Gauge (mm^2): %.f\n', Scu);
fprintf('Connecting Cables Gauge (mm^2): %.f\n', Sconnect);
fprintf('Total Length of Conductors (m): %.f\n', lTotal);
fprintf('Number of Rods: %.f\n', nRods);
fprintf('Maximum Permissible Touch Voltage (V): %.f\n', vTouchMax);
fprintf('Maximum Permissible Step Voltage (V): %.f\n', vStepMax);
fprintf('Grid Touch Voltage (V): %.f\n', vTouchGrid);
fprintf('Grid Step Voltage (V): %.f\n', vStepGrid);
fprintf('Fence Touch Voltage (V): %.f\n', vTouchFence);
fprintf('Grid Resistance (ohm): %.2f\n', rGrid);
fprintf('First Layer Resistivity (ohm x m): %.2f\n', p1);
fprintf('First Layer Depth (m): %.2f \n', h);
fprintf('Second Layer Resistivity (ohm x m): %.2f\n', p2);
figure(1);
plot(aCurve, resistivitiesCurve, 'r', 'linewidth', 2);
hold on;
plot(spacing, resistivities, 'kx', 'linewidth', 2, ...
    'MarkerSize', 9);
hold off;
xmin = -0.5;
xmax = 1.05 * max(spacing);
ymin = 0.75 * min(resistivitiesCurve);
ymax = 1.1 * max(resistivitiesCurve);
xlabel ('a (m)');
ylabel ('\rho (\Omega \times m)')
title ('\rho(a) \times a');
axis([xmin xmax ymin ymax]);