
def OTPdecrypt(h):
    return (((h - 100000) * 469979) % 900000) - 7

def OTPhash(key, msg):
    hash = 2166136261
    prime = 16777619
    for c in key + msg:
        hash ^= ord(c)
        hash %= 18446744073709551616  # force 64-bit arithmetic to match controller
        hash *= prime
        hash %= 18446744073709551616
        hash += 7
        hash %= 18446744073709551616
    # this introduces more collisions, but forces 6-digit output
    hash %= 1000000
    if hash == 0:
        hash += 1
    while hash < 100000:
        hash *= 10
    return hash

def getOTP(c_pass, m_id):
    timeEnc = c_pass
    time = OTPdecrypt(int(timeEnc))
    sn = m_id
    psw = str(OTPhash(sn, str(time)))
    return psw