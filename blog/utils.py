def get_comment_word(count):
    last_digit = count % 10
    last_two_digits = count % 100

    if 11 <= last_two_digits <= 19:
        return f"{count} комментариев"
    elif last_digit == 1:
        return f"{count} комментарий"
    elif 2 <= last_digit <= 4:
        return f"{count} комментария"
    else:
        return f"{count} комментариев"
