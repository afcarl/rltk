import utils

class JaccardIndex(object):

    _similarity = 0

    def __init__(self, set1, set2):
        utils.check_for_none(set1, set2)
        utils.check_for_type(set, set1, set2)

        self._similarity = float(len(set1 & set2)) / float(len(set1 | set2))

    def similarity(self):
        return self._similarity

    def distance(self):
        return 1 - self._similarity
