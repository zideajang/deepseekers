def remove_empty_strings(data):
    if isinstance(data, list):
        # 过滤掉空字符串
        data = [remove_empty_strings(item) for item in data if item != ""]
        return data
    return data
class RecursiveCharacterTextSplitter:
    def __init__(self, chunk_size=400, chunk_overlap=20, separators=["\n\n", "\n", " ", ""]):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators

    def split_text(self, text):
        return self._split_text_recursive(text, self.separators)

    def _split_text_recursive(self, text, separators):
        if not text:
            return []

        if not separators:
            return [text]

        separator = separators[0]
        remaining_separators = separators[1:]
        chunks = []
        if separator == "":
            # 按字符分割
            split_text = list(text)
        else:
            split_text = text.split(separator)
        split_text = remove_empty_strings(split_text)
        for chunk in split_text:
            if len(chunk) <= self.chunk_size:
                if chunk:
                    chunks.append(chunk)
            else:
                chunks.extend(self._split_text_recursive(chunk, remaining_separators))

        return self._merge_chunks(chunks)

    def _merge_chunks(self, chunks):
        merged_chunks = []
        current_chunk = ""
        for chunk in chunks:
            if len(current_chunk) + len(chunk) <= self.chunk_size:
                current_chunk += chunk
            else:
                merged_chunks.append(current_chunk)
                current_chunk = chunk
        if current_chunk:
            merged_chunks.append(current_chunk)
        return merged_chunks