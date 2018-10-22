

class LazyString(object):
    def __init__(self, generate_function):
        self.generate_function = generate_function
        self.generated_value = None

    def __str__(self):
        if not self.generated_value:
            self.generated_value = self.generate_function()
        return self.generated_value

    def __unicode__(self):
        return self.__str__()

    def __repr__(self):
        return self.__str__()
