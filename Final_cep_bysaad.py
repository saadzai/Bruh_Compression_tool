import heapq
import json
import os

# -------------------------------
# HUFFMAN TREE NODE
# -------------------------------
class Node:
    def __init__(self, char, freq):
        self.char = char
        self.freq = freq
        self.left = None
        self.right = None

    def __lt__(self, other):
        return self.freq < other.freq


# -------------------------------
# BUILD FREQUENCY TABLE
# -------------------------------
def build_frequency_table(self, text):
    freq = {}
    for char in text:
        if char not in freq:
            freq[char] = 0
        freq[char] += 1
    return freq


# -------------------------------
# BUILD HUFFMAN TREE
# -------------------------------
def build_huffman_tree(freq_table):
    heap = [Node(char, freq) for char, freq in freq_table.items()]
    heapq.heapify(heap)

    while len(heap) > 1:
        left = heapq.heappop(heap)
        right = heapq.heappop(heap)

        merged = Node(None, left.freq + right.freq)
        merged.left = left
        merged.right = right

        heapq.heappush(heap, merged)

    return heap[0]


# -------------------------------
# GENERATE CODES
# -------------------------------
def generate_codes(node, code="", codes=None):
    if codes is None:
        codes = {}

    if node is None:
        return codes

    # Leaf node found
    if node.char is not None:
        codes[node.char] = code

    generate_codes(node.left, code + "0", codes)
    generate_codes(node.right, code + "1", codes)

    return codes


# -------------------------------
# ENCODE TEXT
# -------------------------------
def encode_text(text, codes):
    temp="".join(codes[ch] for ch in text)
    return temp


# -------------------------------
# PADDING (8 bit)
# -------------------------------
def pad_encoded(encoded):
    extra = (8 - len(encoded) % 8) % 8
    padded_info = f"{extra:08b}"
    encoded += "0" * extra
    return padded_info + encoded, extra


# -------------------------------
# SAVE BINARY STRING TO BYTES FILE
# -------------------------------
def write_binary_file(encoded_str, output_file):
    # Convert 0/1 string → bytes
    b = bytearray()
    for i in range(0, len(encoded_str), 8):
        byte = encoded_str[i:i + 8]
        b.append(int(byte, 2))

    with open(output_file, "wb") as f:
        f.write(b)


# -------------------------------
# DECODEING
# -------------------------------
def remove_padding(encoded_data):
    # First byte → padding info
    padded_info = encoded_data[:8]
    extra_padding = int(padded_info, 2)
    encoded_data = encoded_data[8:]

    if extra_padding > 0:
        encoded_data = encoded_data[:-extra_padding]

    return encoded_data


def decode_text(encoded_data, codes):
    reverse_codes = {v: k for k, v in codes.items()}
    #ulta bana dega key -value ko value key
    current = ""
    decoded = ""

    for bit in encoded_data:
        current += bit
        if current in reverse_codes:
            decoded += reverse_codes[current]
            current = ""

    return decoded


# -------------------------------
# BINARY FILE → BIT STRING
# -------------------------------
def read_binary_as_bits(input_file):
    with open(input_file, "rb") as f:
        byte_data = f.read()

    bits = ""
    for byte in byte_data:
        bits += "{0:08b}".format(byte)

    return bits


# =============================================================
# MAIN FUNCTIONS
# =============================================================

def compress(input_file):
    print("\n--- COMPRESSION STARTED ---")

    if not os.path.exists(input_file):
        print("❌ File not found.")
        return

    with open(input_file, "r") as f:
        text = f.read()

    # Build freq
    freq = build_frequency_table(text)

    # Make tree
    root = build_huffman_tree(freq)

    # Codes
    codes = generate_codes(root)

    # Encode
    encoded = encode_text(text, codes)

    # Padding
    padded_encoded, _ = pad_encoded(encoded)

    # Save encoded data
    output_file = input("Output compressed file name (e.g., output.bin): ")
    write_binary_file(padded_encoded, output_file)

    # Save codes to JSON
    code_file = output_file + "_codes.json"
    with open(code_file, "w") as f:
        json.dump(codes, f, indent=4)

    print("✔ Compression successful!")
    print(f"Compressed file saved as: {output_file}")
    print(f"Codes saved as: {code_file}")


def decompress(encoded_file, codes_file):
    print("\n--- DECOMPRESSION STARTED ---")

    # Load binary data
    bits = read_binary_as_bits(encoded_file)

    # Remove padding
    bits = remove_padding(bits)

    # Load codes
    with open(codes_file, "r") as f:
        codes = json.load(f)

    # Decode
    decoded = decode_text(bits, codes)

    # Save output
    output_file = input("Output decompressed text file name: ")

    with open(output_file, "w") as f:
        f.write(decoded)

    print("✔ Decompression successful!")
    print(f"Decompressed text saved as: {output_file}")


# =============================================================
# MAIN MENU
# =============================================================
if __name__ == "__main__":

    print("-------------------------")
    print(" HUFFMAN CODING PROGRAM")
    print("-------------------------")
    print("1. Compress a file")
    print("2. Decompress a file")
    print("-------------------------")

    choice = input("Choose option (1/2): ").strip()

    if choice == "1":
        file_name = input("Enter file name to compress (press Enter for default sample.txt): ").strip()
        if file_name == "":
            file_name = "sample.txt"
        compress(file_name)

    elif choice == "2":
        encoded_file = input("Enter encoded (.bin) file: ").strip()
        codes_file = input("Enter JSON codes file: ").strip()
        decompress(encoded_file, codes_file)

    else:
        print("Invalid choice.")
