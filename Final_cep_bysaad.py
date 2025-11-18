
###############################################################

import heapq
import json
import os
import io
import zipfile

class Node:
    def __init__(self, char, freq):
        self.char = char
        self.freq = freq
        self.left = None
        self.right = None
    def __lt__(self, other):
        return self.freq < other.freq

def build_frequency_table(text):
    freq = {}
    for char in text:
        freq[char] = freq.get(char, 0) + 1
    return freq

def build_huffman_tree(freq_table):
    if not freq_table:
        return None
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

def generate_codes(node, code="", codes=None):
    if codes is None:
        codes = {}
    if node is None:
        return codes
    if node.char is not None:
        if code == "":
            code = "0"
        codes[node.char] = code
        return codes
    generate_codes(node.left, code + "0", codes)
    generate_codes(node.right, code + "1", codes)
    return codes

def encode_text(text, codes):
    return "".join(codes[ch] for ch in text)

def pad_encoded(encoded):
    extra = (8 - len(encoded) % 8) % 8
    padded_info = f"{extra:08b}"
    encoded += "0" * extra
    return padded_info + encoded, extra

def write_binary_file(encoded_str, output_file):
    b = bytearray()
    for i in range(0, len(encoded_str), 8):
        b.append(int(encoded_str[i:i+8], 2))
    with open(output_file, "wb") as f:
        f.write(b)

def remove_padding(encoded_data):
    padded_info = encoded_data[:8]
    extra_padding = int(padded_info, 2)
    encoded_data = encoded_data[8:]
    if extra_padding > 0:
        encoded_data = encoded_data[:-extra_padding]
    return encoded_data

def decode_text(encoded_data, codes):
    reverse_codes = {v: k for k, v in codes.items()}
    current = ""
    decoded = []
    for bit in encoded_data:
        current += bit
        if current in reverse_codes:
            decoded.append(reverse_codes[current])
            current = ""
    return "".join(decoded)

def read_binary_as_bits(input_file):
    with open(input_file, "rb") as f:
        byte_data = f.read()
    return "".join(f"{byte:08b}" for byte in byte_data)

def compress(input_file):
    print("\n--- COMPRESSION ---")
    if not os.path.exists(input_file):
        print("File not found.")
        return
    with open(input_file, "r") as f:
        text = f.read()
    if not text:
        print("File empty.")
        return
    freq = build_frequency_table(text)
    root = build_huffman_tree(freq)
    codes = generate_codes(root)
    encoded = encode_text(text, codes)
    padded_encoded, _ = pad_encoded(encoded)
    out_name = input("Output .bin file name (default output.bin): ").strip() or "output.bin"
    write_binary_file(padded_encoded, out_name)
    with open(out_name + "_codes.json", "w") as f:
        json.dump(codes, f, indent=2)
    print("Done.")

def decompress(encoded_file, codes_file):
    print("\n--- DECOMPRESSION ---")
    if not (os.path.exists(encoded_file) and os.path.exists(codes_file)):
        print("Missing file.")
        return
    bits = read_binary_as_bits(encoded_file)
    bits = remove_padding(bits)
    with open(codes_file, "r") as f:
        codes = json.load(f)
    text = decode_text(bits, codes)
    out_name = input("Output .txt file name (default decompressed.txt): ").strip() or "decompressed.txt"
    with open(out_name, "w") as f:
        f.write(text)
    print("Done.")

# ---------------- Streamlit (simple) ----------------
try:
    import streamlit as st
    import io
    import zipfile

    def _bits_to_bytes(bitstring):
        return bytes(int(bitstring[i:i+8], 2) for i in range(0, len(bitstring), 8))
    def _bytes_to_bits(data):
        return "".join(f"{b:08b}" for b in data)

    def _compress_text(text):
        if not text:
            raise ValueError("Empty text.")
        freq = build_frequency_table(text)
        root = build_huffman_tree(freq)
        codes = generate_codes(root)
        encoded = encode_text(text, codes)
        padded, _ = pad_encoded(encoded)
        return _bits_to_bytes(padded), codes

    def _decompress_bytes(bin_bytes, codes):
        bits = _bytes_to_bits(bin_bytes)
        bits = remove_padding(bits)
        return decode_text(bits, codes)

    def _streamlit_app():
        st.title("Huffman Compressor")
        mode = st.radio("Mode", ["Compress", "Decompress"])

        if mode == "Compress":
            up = st.file_uploader("Upload text file", type=["txt"])
            if up and st.button("Compress"):
                try:
                    # Read once, keep original size in bytes
                    raw = up.read()
                    text = raw.decode("utf-8", errors="ignore")
                    bin_bytes, codes = _compress_text(text)

                    # Stats
                    orig_size = len(raw)
                    comp_size = len(bin_bytes)
                    ratio = (comp_size / orig_size) if orig_size else 0.0
                    reduction = (1 - ratio) * 100 if orig_size else 0.0

                    # Build ZIP: .bin + codes.json
                    base = up.name.rsplit(".", 1)[0] if "." in up.name else up.name
                    zip_buf = io.BytesIO()
                    with zipfile.ZipFile(zip_buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
                        zf.writestr(f"{base}.bin", bin_bytes)
                        zf.writestr(f"{base}_codes.json", json.dumps(codes, indent=2))
                    zip_buf.seek(0)

                    st.success("Compressed.")
                    st.write(f"Original: {orig_size} bytes, Compressed: {comp_size} bytes")
                    st.write(f"Compression ratio: {ratio:.3f}x, Reduction: {reduction:.2f}%")

                    st.download_button(
                        "Download compressed.zip",
                        data=zip_buf.getvalue(),
                        file_name=f"{base}_compressed.zip",
                        mime="application/zip",
                    )
                except Exception as e:
                    st.error(e)

        else:
            bin_up = st.file_uploader("Upload .bin", type=["bin"])
            codes_up = st.file_uploader("Upload codes.json", type=["json"])
            if bin_up and codes_up and st.button("Decompress"):
                try:
                    bin_bytes = bin_up.read()
                    codes = json.loads(codes_up.read().decode("utf-8", errors="ignore"))
                    text = _decompress_bytes(bin_bytes, codes)

                    # Stats (relative to decompressed size)
                    comp_size = len(bin_bytes)
                    decomp_size = len(text.encode("utf-8"))
                    ratio = (comp_size / decomp_size) if decomp_size else 0.0
                    reduction = (1 - ratio) * 100 if decomp_size else 0.0

                    # Build ZIP: decompressed.txt
                    base = bin_up.name.rsplit(".", 1)[0] if "." in bin_up.name else bin_up.name
                    zip_buf = io.BytesIO()
                    with zipfile.ZipFile(zip_buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
                        zf.writestr(f"{base}_decompressed.txt", text)
                    zip_buf.seek(0)

                    st.success("Decompressed.")
                    st.write(f"Compressed: {comp_size} bytes, Decompressed: {decomp_size} bytes")
                    st.write(f"Compression ratio (comp/decomp): {ratio:.3f}x, Reduction: {reduction:.2f}%")
                    st.text_area("Text preview", text[:5000], height=200)

                    st.download_button(
                        "Download decompressed.zip",
                        data=zip_buf.getvalue(),
                        file_name=f"{base}_decompressed.zip",
                        mime="application/zip",
                    )
                except Exception as e:
                    st.error(e)

    if __name__ == "__main__":
        _streamlit_app()
except Exception:
    pass



###################################################################3
# import heapq
# import json
# import os

# # -------------------------------
# # HUFFMAN TREE NODE
# # -------------------------------
# class Node:
#     def __init__(self, char, freq):
#         self.char = char
#         self.freq = freq
#         self.left = None
#         self.right = None

#     def __lt__(self, other):
#         return self.freq < other.freq


# # -------------------------------
# # BUILD FREQUENCY TABLE
# # -------------------------------
# def build_frequency_table(text):
#     freq = {}
#     for char in text:
#         if char not in freq:
#             freq[char] = 0
#         freq[char] += 1
#     return freq


# # -------------------------------
# # BUILD HUFFMAN TREE
# # -------------------------------
# def build_huffman_tree(freq_table):
#     if not freq_table:
#         return None
#     heap = [Node(char, freq) for char, freq in freq_table.items()]
#     heapq.heapify(heap)
#     while len(heap) > 1:
#         left = heapq.heappop(heap)
#         right = heapq.heappop(heap)
#         merged = Node(None, left.freq + right.freq)
#         merged.left = left
#         merged.right = right
#         heapq.heappush(heap, merged)
#     return heap[0]


# # -------------------------------
# # GENERATE CODES
# # -------------------------------
# def generate_codes(node, code="", codes=None):
#     if codes is None:
#         codes = {}
#     if node is None:
#         return codes
#     # Leaf node
#     if node.char is not None:
#         if code == "":  # handle single-symbol inputs
#             code = "0"
#         codes[node.char] = code
#         return codes
#     generate_codes(node.left, code + "0", codes)
#     generate_codes(node.right, code + "1", codes)
#     return codes


# # -------------------------------
# # ENCODE TEXT
# # -------------------------------
# def encode_text(text, codes):
#     temp="".join(codes[ch] for ch in text)
#     return temp


# # -------------------------------
# # PADDING (8 bit)
# # -------------------------------
# def pad_encoded(encoded):
#     extra = (8 - len(encoded) % 8) % 8
#     padded_info = f"{extra:08b}"
#     encoded += "0" * extra
#     return padded_info + encoded, extra


# # -------------------------------
# # SAVE BINARY STRING TO BYTES FILE
# # -------------------------------
# def write_binary_file(encoded_str, output_file):
#     # Convert 0/1 string → bytes
#     b = bytearray()
#     for i in range(0, len(encoded_str), 8):
#         byte = encoded_str[i:i + 8]
#         b.append(int(byte, 2))

#     with open(output_file, "wb") as f:
#         f.write(b)


# # -------------------------------
# # DECODEING
# # -------------------------------
# def remove_padding(encoded_data):
#     # First byte → padding info
#     padded_info = encoded_data[:8]
#     extra_padding = int(padded_info, 2)
#     encoded_data = encoded_data[8:]

#     if extra_padding > 0:
#         encoded_data = encoded_data[:-extra_padding]

#     return encoded_data


# def decode_text(encoded_data, codes):
#     reverse_codes = {v: k for k, v in codes.items()}
#     #ulta bana dega key -value ko value key
#     current = ""
#     decoded = ""

#     for bit in encoded_data:
#         current += bit
#         if current in reverse_codes:
#             decoded += reverse_codes[current]
#             current = ""

#     return decoded


# # -------------------------------
# # BINARY FILE → BIT STRING
# # -------------------------------
# def read_binary_as_bits(input_file):
#     with open(input_file, "rb") as f:
#         byte_data = f.read()

#     bits = ""
#     for byte in byte_data:
#         bits += "{0:08b}".format(byte)

#     return bits


# # =============================================================
# # MAIN FUNCTIONS
# # =============================================================

# def compress(input_file):
#     print("\n--- COMPRESSION STARTED ---")
#     if not os.path.exists(input_file):
#         print("❌ File not found.")
#         return
#     with open(input_file, "r", encoding="utf-8") as f:
#         text = f.read()
#     if not text:
#         print("❌ File is empty.")
#         return
#     freq = build_frequency_table(text)
#     root = build_huffman_tree(freq)
#     if root is None:
#         print("❌ Nothing to encode.")
#         return
#     codes = generate_codes(root)
#     encoded = encode_text(text, codes)
#     padded_encoded, _ = pad_encoded(encoded)
#     output_file = input("Output compressed file name (e.g., output.bin): ").strip()
#     if not output_file:
#         output_file = "output.bin"
#     write_binary_file(padded_encoded, output_file)
#     code_file = output_file + "_codes.json"
#     with open(code_file, "w", encoding="utf-8") as f:
#         json.dump(codes, f, indent=4, ensure_ascii=False)
#     print("✔ Compression successful!")
#     print(f"Compressed file saved as: {output_file}")
#     print(f"Codes saved as: {code_file}")


# def decompress(encoded_file, codes_file):
#     print("\n--- DECOMPRESSION STARTED ---")
#     if not (os.path.exists(encoded_file) and os.path.exists(codes_file)):
#         print("❌ One or both files not found.")
#         return
#     bits = read_binary_as_bits(encoded_file)
#     bits = remove_padding(bits)
#     with open(codes_file, "r", encoding="utf-8") as f:
#         codes = json.load(f)
#     # Basic validation
#     if not codes:
#         print("❌ Codes file empty or invalid.")
#         return
#     decoded = decode_text(bits, codes)
#     output_file = input("Output decompressed text file name: ").strip()
#     if not output_file:
#         output_file = "decompressed.txt"
#     with open(output_file, "w", encoding="utf-8") as f:
#         f.write(decoded)
#     print("✔ Decompression successful!")
#     print(f"Decompressed text saved as: {output_file}")


# # =============================================================
# # STREAMLIT APP (optional UI)
# # =============================================================
# # Run via: streamlit run "c:\Users\SAAD ZAI\OneDrive\Documents\Saad's codes\dsa\Final_cep_bysaad.py"
# try:
#     import streamlit as st
#     import io

#     def _bits_to_bytes(bitstring: str) -> bytes:
#         out = bytearray()
#         for i in range(0, len(bitstring), 8):
#             out.append(int(bitstring[i:i+8], 2))
#         return bytes(out)

#     def _bytes_to_bits(data: bytes) -> str:
#         return "".join(f"{b:08b}" for b in data)

#     def _compress_text(text: str):
#         if text is None or text == "":
#             raise ValueError("Empty input text.")
#         freq = build_frequency_table(text)
#         if not freq:
#             raise ValueError("No symbols to encode.")
#         root = build_huffman_tree(freq)
#         codes = generate_codes(root)
#         encoded = encode_text(text, codes)
#         padded, _ = pad_encoded(encoded)
#         return _bits_to_bytes(padded), codes

#     def _decompress_bytes(bin_bytes: bytes, codes: dict) -> str:
#         if not bin_bytes:
#             raise ValueError("Empty binary input.")
#         bits = _bytes_to_bits(bin_bytes)
#         bits = remove_padding(bits)
#         return decode_text(bits, codes)

#     def _streamlit_app():
#         st.set_page_config(page_title="Huffman Compressor", page_icon="🗜️", layout="centered")
#         st.title("Huffman Coding: Compress / Decompress")

#         tab_c, tab_d = st.tabs(["Compress", "Decompress"])

#         with tab_c:
#             st.subheader("Compress a text file")
#             enc = st.selectbox("Text encoding", ["utf-8", "latin-1"], index=0)
#             up = st.file_uploader("Upload a text file", type=["txt", "md", "csv", "log", "json"])
#             if up is not None:
#                 try:
#                     text = up.read().decode(enc)
#                 except Exception as e:
#                     st.error(f"Failed to decode with {enc}: {e}")
#                     text = None

#                 if text is not None:
#                     st.write(f"Characters: {len(text):,}")
#                     if st.button("Compress"):
#                         try:
#                             bin_bytes, codes = _compress_text(text)
#                             orig_size = len(text.encode(enc))
#                             comp_size = len(bin_bytes)
#                             ratio = (comp_size / orig_size) if orig_size else 0.0

#                             st.success("Compression successful.")
#                             col1, col2, col3 = st.columns(3)
#                             col1.metric("Original (bytes)", f"{orig_size:,}")
#                             col2.metric("Compressed (bytes)", f"{comp_size:,}")
#                             col3.metric("Ratio", f"{ratio:.3f}x")

#                             base = up.name.rsplit(".", 1)[0] if "." in up.name else up.name
#                             bin_name = f"{base}.bin"
#                             json_name = f"{base}_codes.json"

#                             st.download_button(
#                                 "Download compressed .bin",
#                                 data=bin_bytes,
#                                 file_name=bin_name,
#                                 mime="application/octet-stream",
#                             )
#                             st.download_button(
#                                 "Download codes .json",
#                                 data=json.dumps(codes, ensure_ascii=False, indent=2),
#                                 file_name=json_name,
#                                 mime="application/json",
#                             )
#                         except Exception as e:
#                             st.error(f"Compression failed: {e}")

#         with tab_d:
#             st.subheader("Decompress")
#             bin_up = st.file_uploader("Upload .bin file", type=["bin"], key="bin_up")
#             json_up = st.file_uploader("Upload codes .json", type=["json"], key="json_up")

#             if bin_up is not None and json_up is not None and st.button("Decompress"):
#                 try:
#                     bin_bytes = bin_up.read()
#                     codes = json.loads(json_up.read().decode("utf-8"))
#                     text = _decompress_bytes(bin_bytes, codes)

#                     st.success("Decompression successful.")
#                     st.text_area("Preview", value=text[:5000], height=200)
#                     st.download_button(
#                         "Download decompressed .txt",
#                         data=text.encode("utf-8"),
#                         file_name="decompressed.txt",
#                         mime="text/plain; charset=utf-8",
#                     )
#                 except Exception as e:
#                     st.error(f"Decompression failed: {e}")
#             elif bin_up is None or json_up is None:
#                 st.info("Upload both the .bin and the codes .json to enable decompression.")

#     # Only run the UI when executed by Streamlit
#     if __name__ == "__main__":
#         _streamlit_app()

# except Exception:
#     # Streamlit not installed or not running under Streamlit; ignore.
#     pass





###############################################################################################################################################






