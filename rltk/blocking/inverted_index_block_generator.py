import os
import time
import tempfile

from rltk.blocking import BlockGenerator
from rltk.io.reader import BlockFileReader
from rltk.io.writer import BlockFileWriter


class InvertedIndexBlockGenerator(BlockGenerator):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._tokenizer = self._kwargs.get('tokenizer')
        self._tokenizer1 = self._kwargs.get('tokenizer1', self._tokenizer)
        self._tokenizer2 = self._kwargs.get('tokenizer2', self._tokenizer)
        self._buffer_size = self._kwargs.get('buffer_size') or 10000

    def _generate_blocks(self):

        temp_file_prefix = os.path.join(tempfile.gettempdir(), str(time.time()))
        ds1_temp_filename = temp_file_prefix + '.ds1.temp'
        ds2_temp_filename = temp_file_prefix + '.ds2.temp'

        # normal indices (id: tokens)
        ds1_temp_writer = BlockFileWriter(ds1_temp_filename, buffer_size=self._buffer_size)
        for r1 in self._dataset1:
            tokens = self._tokenizer1(r1)
            for t in tokens:
                ds1_temp_writer.write(r1.id, t)
        ds1_temp_writer.close()

        # inverted indices (token: ids)
        ds2_temp_writer = BlockFileWriter(ds2_temp_filename, buffer_size=self._buffer_size)
        for r2 in self._dataset2:
            tokens = self._tokenizer2(r2)
            for t in tokens:
                ds2_temp_writer.write(t, r2.id)
        ds2_temp_writer.close()

        # construct blocks
        ds2_iter = iter(BlockFileReader(ds2_temp_filename))
        eof = False
        while not eof:
            # read a chunk of data from ds2 into memory
            ds2_indices = dict()
            count = self._buffer_size
            while count > 0:
                next_value = next(ds2_iter, None)
                if not next_value:
                    eof = True
                    break

                t, id2 = next_value
                if not t in ds2_indices:
                    ds2_indices[t] = set()
                ds2_indices[t] = ds2_indices[t] | set([id2])
                count -= 1

            # scan on-disk ds1 and in-memory ds2 chunk and make pairs
            ds1_temp_reader = BlockFileReader(ds1_temp_filename)
            for id1, t in ds1_temp_reader:
                if t in ds2_indices:
                    for id2 in ds2_indices[t]:
                        self._writer.write(id1, id2)
