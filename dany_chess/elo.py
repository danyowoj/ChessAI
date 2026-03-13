def update_elo(rating_a, rating_b, score_a, k=32):

    expected_a = 1 / (1 + 10 ** ((rating_b - rating_a) / 400))

    new_rating_a = rating_a + k * (score_a - expected_a)

    return new_rating_a
