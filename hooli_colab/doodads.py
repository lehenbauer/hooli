""" assorted doodads for hooli """

from flask import current_app

def rating_to_stars(rating, max_rating=5):
    """
    Returns a string representation of a star rating.
    Args:
        rating (float): The rating value to be converted into stars.
        max_rating (int, optional): The maximum possible rating. Defaults to 5.
    Returns:
        str: A string of star characters representing the rating, where filled stars (★)
             represent full points, half stars (⭐) represent half points, and empty stars (☆)
             represent no points.
    """
    filled_star = "★"
    half_star = "⭐"
    empty_star = "☆"

    stars = ""
    for i in range(1, max_rating + 1):
        if rating >= i:
            stars += filled_star
        elif rating >= i - 0.5:
            stars += half_star
        else:
            stars += empty_star
    return stars

def log_message(message, *args, level="info"):
    """ log a message to the application logger """
    if level.lower() == 'info':
        current_app.logger.info(message, *args)
    elif level.lower() == 'warning':
        current_app.logger.warning(message, *args)
    elif level.lower() == 'error':
        current_app.logger.error(message, *args)
    else:
        current_app.logger.debug(message, *args)
