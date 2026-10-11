import matplotlib.pyplot as plt


def codificar_nrz_polar(VCC, input):
    output = []
    output = [-VCC if i==0 else VCC for i in input]
    return output    
    

def decodificar_nrz_polar(VCC, input):
    output = []
    output = [0 if i== -VCC else 1 for i in input]
    return output
