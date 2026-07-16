p = ["r", "l", "f"]
last = []



while True:
  
    for i in range(len(p)):
        x = input("input X: ")
        print(i)
        if not last or x != last[-1]:
            last.append(x)
            print(last) 
            # if x == p[i]:

            
                





