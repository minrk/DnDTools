from pylab import *
from numpy import *
from random import randint

def rolls(n,d,bonus,trials=1e5):
    A = zeros(n*d+bonus+1)
    # therolls = random.randint(bonus)
    for i in range(int(trials)):
        x = bonus
        for j in range(n):
            x += randint(1,d)
        A[x] += 1
    return A/A.sum()

def rollmax(n,d,bonus,trials=1e5):
    A = zeros(d+bonus+1)
    # therolls = random.randint(bonus)
    for i in range(int(trials)):
        rolls = [randint(1,d) for i in range(n)]
        x = bonus + max(rolls)
        A[x] += 1
    return A/A.sum()

def tworoll(d):
    ps = zeros(d+1)
    df = 1.*d
    d2 = 1.*d*d
    for i in range(1,d+1):
        p = 1./d2
        p += 2.*(i-1.)/d2
        ps[i] = p
    return ps

def barr(Y,Z,step=1):
    N = len(Y)
    x = arange(0,N+1,step)-.5
    print N,x
    figure()
    y = []
    z = []
    for i in range(len(x)):
        y.append(sum(Y[i*step:(i+1)*step]))
        z.append(sum(Z[i*step:(i+1)*step]))
    print x.shape, len(y),len(z)
    bar(x,z,width=step,color='g',label='1d12')
    bar(x,y,width=step,color='b',label='2d6',alpha=0.75)
    xlabel("roll")
    ylabel("probability (%)")
    legend(loc=0)
    xlim(0,len(x)+1)

def pdf(Y,Z):
    y = [0]+[sum(Y[:i+1]) for i in range(len(Y))]
    z = [0]+[sum(Z[:i+1]) for i in range(len(Z))]
    
    y,z = map(array, (y,z))
    x = arange(0,len(y))
    figure()
    plot(x+1,100*(1-y),x+1,100*(1-z))
    xlim(0,None)
    xlabel("x")
    ylabel("probability (%)")
    title("probability that a roll will be at least x")
    legend(["2d6", "1d12"],loc=0)
    grid(True)

def pdfz(Y):
    # y = [sum(Y[:i]) for i in range(len(Y))]
    y = [0]+list(cumsum(Y))[:-1]
    # z = [0]+[sum(Z[:i+1]) for i in range(len(Z))]
    
    # y,z = map(array, (y,z))
    y = array(y)
    x = arange(0,len(y))
    # figure()
    plot(x,100*(1-y))
    xlim(0,None)
    ylim(0,100)
    xlabel("x")
    ylabel("probability (%)")
    title("probability that a roll will be at least x")
    # legend(["2d6", "1d12"],loc=0)
    yticks(arange(0,101,10))
    grid(True)

def multi_pdf(*Ys):
    figure()
    for y in Ys:
        pdfz(y)

def means(Y,Z):
    x = arange(1,len(Y)+1)
    print sum(x*Y)/100.,sum(x*Z)/100.

def save(bonus=0, threshold=1e-3, first=False, demand=0):
    """Return the probability that a save will be made on each given turn.
    The cumulative sum (numpy.cumsum()) will be the probability of the number
    of rounds that the effect will have lasted.
    
    if demand > 0, Justice will be Demanded when the first save is failed
    if demand < 0, Justice will be Demanded when the first save is made
    """
    p = (11.+bonus)/20
    pi = 1.-p
    if first:
        probs = [p]
        i=1
    else:
        probs = [0]
        i=0
        if demand:
            justice = 1
        else:
            justice = 0
    cs = sum(probs)
    while 1-cs > threshold:
        s = p*(1-justice)
        if demand > 0:
            s += justice*p*pi
            justice *= pi
        elif demand < 0:
            s += justice*p*p
            justice *= p
        # p0 = probs[-1]
        s = (1.-cs)*s
        probs.append(s)
        cs += s
        i+=1
    return probs

def expect(lis):
    """compute the expectation value of a list of probabilities, e.g. the output of save."""
    s = 0.
    for i,p in enumerate(lis):
        s += i*p
    return s

def plot_durations(bonuses):
    figure()
    for b in bonuses:
        pdfz(save(b))
    xlim(0,10)
    xticks(arange(0,11))
    xlabel("turns")
    title("probability that an effect will survive at least x turns.")
    legend(map(str, bonuses), loc=0)


# # of attacks it will take

def roll_damage(tohit=.5, base=10,var=2, max_turns = 3):
    turns = {0:(zeros(1),ones(1))}
    max_d = base+var
    values = arange(max_d*max_turns+1)
    p = tohit/(2.*var+1.)
    probs = zeros(max_d+1)
    probs[0] = 1.-tohit
    probs[base-var:base+var+1] = p
    for i in range(1,max_turns+1):
        last = turns[i-1]
        l_damage, l_probs = last
        last_n = (i-1)*max_d + 1
        new_n = last_n+max_d
        new_damage = arange(new_n)
        new_probs = zeros(new_n)
        # new_probs[:last_n] = l_probs*(1.-tohit)
        for n in range(last_n):
            for d in range(max_d+1):
                new_probs[n+d] += l_probs[n]*probs[d]
        print i,sum(new_probs)
        turns[i] = (new_damage,new_probs)
    return turns

def plot_turns(turndict, pcs=4):
    figure()
    turns = sorted(turndict.keys())
    for t in turns[::pcs]:
        print t
        pdfz(turndict[t][1])
    grid(True)
    title("Probability of %i PCs doing x damage"%pcs)
    xlim(0,500)

    
