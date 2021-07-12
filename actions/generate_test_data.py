from st2common.runners.base_action import Action


class GenerateTestData(Action):
    PAYLOAD_DATA = 'A' * (1 << 10)

    def run(self, count):
        return [{
            'index': count,
            'payload': self.PAYLOAD_DATA
        } for x in range(count)]
