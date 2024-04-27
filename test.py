def test(voltage, capacity, phase):
    if phase == "Y":
        voltage = voltage / (3 ** (0.5))
        current = capacity / voltage / 3
        print("3 phase Y : ", current)
    elif phase == "delta":
        voltage = voltage
        current = capacity / (voltage / (3 ** (0.5))) / 3
        print("3 phase delta : ", current)


test(20, 5, "Y")
test(20, 5, "delta")
