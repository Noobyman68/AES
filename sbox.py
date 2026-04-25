#originally written in c and then translated

#xor for addition/subtraction
#and for bit multiplication
#polynomial reduction for actual multiplication

mx = 0x11B


def degree(num):
    if num == 0:
        return -1
    return num.bit_length() - 1


def poly_div(a, b):
    if b == 0:
        return None

    q = 0
    r = a

    while r != 0 and degree(r) >= degree(b):
        shift = degree(r) - degree(b)
        q ^= (1 << shift)
        r ^= (b << shift)

    return [q, r]


def poly_inverse(a, b):
    if a == 0:
        return 0

    r0, r1 = b, a
    t0, t1 = 0, 1

    while r1 != 0:
        q, _ = poly_div(r0, r1)
        r0, r1 = r1, r0 ^ poly_mult(q, r1)
        t0, t1 = t1, t0 ^ poly_mult(q, t1)

    return t0 & 0xFF


def poly_mult(a, b):
    result = 0
    while b:
        if b & 1:
            result ^= a
        a <<= 1
        b >>= 1
    return result


def vector_mult(row, vec):
    result = 0
    for i in range(8):
        result ^= (row[i] & vec[i])
    return result


def matrix_mult(matrix, vector):
    result = [0] * 8
    for i in range(8):
        result[i] = vector_mult(matrix[i], vector)
    return result


def int_to_vector(x):
    result = [0] * 8
    for i in range(8):
        result[i] = (x>>i) & 1
    return result


def vector_to_int(v):
    result = 0
    #work backwords to maintain order
    for i in range(7, -1, -1):
        result = (result << 1) | v[i]
    return result


def calculate_sbox():
    sbox = [0] * 256

    matrix = [
        [1,0,0,0,1,1,1,1],
        [1,1,0,0,0,1,1,1],
        [1,1,1,0,0,0,1,1],
        [1,1,1,1,0,0,0,1],
        [1,1,1,1,1,0,0,0],
        [0,1,1,1,1,1,0,0],
        [0,0,1,1,1,1,1,0],
        [0,0,0,1,1,1,1,1]
    ]

    for i in range(256):
        inv = poly_inverse(i, mx)

        vec = int_to_vector(inv)
        result = matrix_mult(matrix, vec)

        val = vector_to_int(result)
        val ^= 0x63

        sbox[i] = val

    return sbox


def calculate_isbox():
    isbox = [0] * 256

    matrix = [
        [0,0,1,0,0,1,0,1],
        [1,0,0,1,0,0,1,0],
        [0,1,0,0,1,0,0,1],
        [1,0,1,0,0,1,0,0],
        [0,1,0,1,0,0,1,0],
        [0,0,1,0,1,0,0,1],
        [1,0,0,1,0,1,0,0],
        [0,1,0,0,1,0,1,0]
    ]

    for i in range(256):
        vec = int_to_vector(i)

        result = matrix_mult(matrix, vec)
        val = vector_to_int(result)
        val ^= 0x05

        inv = poly_inverse(val, mx)
        isbox[i] = inv

    return isbox


if __name__ == "__main__":
    sbox = calculate_sbox()
    isbox = calculate_isbox()

    print("S-box (first 16):", sbox[:16])
    print("Inverse S-box (first 16):", isbox[:16])
