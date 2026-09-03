import cv2


def median_filter(image, kernel_size=5):
	"""Apply a median filter to an image before it is displayed."""
	if image is None or image.size == 0:
		return image

	if kernel_size < 3 or kernel_size % 2 == 0:
		raise ValueError("kernel_size must be an odd number greater than or equal to 3")

	return cv2.medianBlur(image, kernel_size)
