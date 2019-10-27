function f = stratificationFunction(x)

a = getA;
resistivities = getResistivities;

f = 0;

for i = 1:length(a)
    sum = 0;
    
    for n = 1:25
        sum = sum + (x(2) ^ n) / sqrt(1 + ((2 * n * x(3)) / a(i)) ^ 2)...
            - (x(2) ^ n) / sqrt(4 + ((2 * n * x(3)) / a(i)) ^ 2);
    end
    
    f = f + (resistivities(i) - x(1) * (4 * sum + 1)) ^ 2;
    
end

end