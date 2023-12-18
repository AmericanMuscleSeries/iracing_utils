from trueskill import Rating

class Driver:
    iracing_id = int()
    finishes = list()
    rating = Rating()
    
    
    def __init__(self, tokens):
        self.iracing_id = tokens[0]
        self.finishes = tokens[3:]

        if float(tokens[1]) != 0 or float(tokens[2]) != 0:
            mu = float(tokens[1])
            sigma = float(tokens[2])
            self.rating = Rating(mu=mu, sigma=sigma)
    
    
    def update(self, rating):
        self.rating = rating

    
    def to_file(self):
        tokens = [str(self.iracing_id), str(self.rating.mu), str(self.rating.sigma), ','.join(map(str, self.finishes))]
        
        return tokens

    
    __update = update
        