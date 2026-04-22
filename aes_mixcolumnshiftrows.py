def get_degree(bits):
    for i in range(len(bits)):
        if bits[i] == 1:
            return len(bits) - 1 - i
    return -1

def xor_bits(a, b):
    # Pad shorter list with leading zeros to match the longer one
    max_len = max(len(a), len(b))
    padded_a = [0] * (max_len - len(a)) + a
    padded_b = [0] * (max_len - len(b)) + b
    return [padded_a[i] ^ padded_b[i] for i in range(max_len)]

def shift_left(bits, k):
    return bits[k:] + [0] * k

def divide_galois(A, M):
    A = A[:]  # copy

    # Ensure A is long enough to hold M, pad with leading zeros if A is shorter
    if len(A) < len(M):
        A = [0] * (len(M) - len(A)) + A

    while get_degree(A) >= get_degree(M) and any(A):
        shift = get_degree(A) - get_degree(M)

        # Shift M to align with A's leading bit
        shifted_M = shift_left(M, shift)

        # Ensure shifted_M is same length as A for xor_bits
        if len(shifted_M) < len(A):
            shifted_M = [0] * (len(A) - len(shifted_M)) + shifted_M
        elif len(shifted_M) > len(A):
            A = [0] * (len(shifted_M) - len(A)) + A

        A = xor_bits(A, shifted_M)

    # Remove leading zeros if necessary, but keep at least one bit for 0
    while len(A) > 1 and A[0] == 0:
        A = A[1:]
    return A

# The irreducible polynomial for GF(2^8) in AES: x^8 + x^4 + x^3 + x + 1 (0x11B)
# Represented as a list of bits for a 9-degree polynomial (degree 8)
AES_MODULUS_BITS = [1, 0, 0, 0, 1, 1, 0, 1, 1]

def multiply_galois(A_bits, B_bits, modulus_bits=AES_MODULUS_BITS):
    # For two 8-bit polynomials, the product can be up to degree 14 (15 bits).
    # Initialize intermediate_result with enough space.
    intermediate_result_len = len(A_bits) + len(B_bits) - 1
    intermediate_result = [0] * intermediate_result_len if intermediate_result_len > 0 else [0]

    # Iterate B_bits from LSB to MSB (right to left) for multiplication
    for i in range(len(B_bits)):
        # Check i-th bit from the right
        if B_bits[len(B_bits) - 1 - i] == 1:
            # XOR A_bits shifted left by i with intermediate_result
            shifted_A = shift_left(A_bits, i)
            intermediate_result = xor_bits(intermediate_result, shifted_A)

    # After multiplication, reduce modulo modulus_bits
    return divide_galois(intermediate_result, modulus_bits)

# helper function, makes it easier to input the binary shortcut values directly
def int_to_bits(x, size=8):
    bits = []
    for i in range(size - 1, -1, -1):
        power = 1 << i
        if x >= power:
            bits.append(1)
            x -= power
        else:
            bits.append(0)
    return bits

# New helper function to convert a bit list to an integer
def bits_to_int(bits):
    val = 0
    # Assuming bits are MSB first (e.g., [1,0,1] is 5)
    for bit in bits:
        val = (val << 1) | bit
    return val

def mix_columns(state):
    # Performs the Mix Columns operation on the AES state matrix.
    # State is a 4x4 matrix of bytes (integers).
    mixed_state = [[0 for _ in range(4)] for _ in range(4)]
    mix_matrix = [
        [0x02, 0x03, 0x01, 0x01],
        [0x01, 0x02, 0x03, 0x01],
        [0x01, 0x01, 0x02, 0x03],
        [0x03, 0x01, 0x01, 0x02]
    ]

    for c in range(4):
        for r in range(4):
            # Each element in the new column is a dot product of a row from the mix_matrix
            # and the current column of the state matrix, using Galois multiplication.
            # Convert integers to 8-bit lists, perform multiplication, then convert back to int
            val1 = bits_to_int(multiply_galois(int_to_bits(mix_matrix[r][0], 8), int_to_bits(state[0][c], 8)))
            val2 = bits_to_int(multiply_galois(int_to_bits(mix_matrix[r][1], 8), int_to_bits(state[1][c], 8)))
            val3 = bits_to_int(multiply_galois(int_to_bits(mix_matrix[r][2], 8), int_to_bits(state[2][c], 8)))
            val4 = bits_to_int(multiply_galois(int_to_bits(mix_matrix[r][3], 8), int_to_bits(state[3][c], 8)))

            mixed_state[r][c] = val1 ^ val2 ^ val3 ^ val4
    return mixed_state

def inv_mix_columns(state):
    # Performs the Inverse Mix Columns operation on the AES state matrix.
    # State is a 4x4 matrix of bytes (integers).
    inv_mixed_state = [[0 for _ in range(4)] for _ in range(4)]
    inv_mix_matrix = [
        [0x0E, 0x0B, 0x0D, 0x09],
        [0x09, 0x0E, 0x0B, 0x0D],
        [0x0D, 0x09, 0x0E, 0x0B],
        [0x0B, 0x0D, 0x09, 0x0E]
    ]

    for c in range(4):
        for r in range(4):
            # Convert integers to 8-bit lists, perform multiplication, then convert back to int
            val1 = bits_to_int(multiply_galois(int_to_bits(inv_mix_matrix[r][0], 8), int_to_bits(state[0][c], 8)))
            val2 = bits_to_int(multiply_galois(int_to_bits(inv_mix_matrix[r][1], 8), int_to_bits(state[1][c], 8)))
            val3 = bits_to_int(multiply_galois(int_to_bits(inv_mix_matrix[r][2], 8), int_to_bits(state[2][c], 8)))
            val4 = bits_to_int(multiply_galois(int_to_bits(inv_mix_matrix[r][3], 8), int_to_bits(state[3][c], 8)))

            inv_mixed_state[r][c] = val1 ^ val2 ^ val3 ^ val4
    return inv_mixed_state

def print_state_matrix(state, title="State Matrix"):
    # Prints a 4x4 matrix of bytes in hexadecimal format.

    # state (list of lists): The 4x4 state matrix of integers.
    # title (str): An optional title for the output.
    print(f"\n{title}:")
    for row in state:
        print([f'{byte:02X}' for byte in row])

initial_state = [
    [0xDB, 0xF2, 0xD4, 0x1B],
    [0x13, 0x0D, 0x5C, 0x75],
    [0x51, 0x6E, 0xB6, 0x7E],
    [0x00, 0x6E, 0x0D, 0x5C]
]

print_state_matrix(initial_state, "Initial State")

mixed_state = mix_columns(initial_state)
print_state_matrix(mixed_state, "Mixed State")

inv_mixed_state = inv_mix_columns(mixed_state)
print_state_matrix(inv_mixed_state, "Inverse Mixed State (should match Initial State)")

# Verify if the inverse operation returns the original state
if initial_state == inv_mixed_state:
    print("\nVerification successful: Inverse Mix Columns correctly reversed Mix Columns.")
else:
    print("\nVerification failed: Inverse Mix Columns did NOT return the original state.")