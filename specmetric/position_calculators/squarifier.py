import squarify
import pandas as pd

def squarify_within_bar(values, width, height, pad=True):
  """Uses the squarify package (https://github.com/laserson/squarify)
  to get coordinates for squares that fit within a bar of 
  width=width and height=height.  Returns df with locations and
  distances relative to the top left of the bar
  """
  # these values define the coordinate system for the returned rectangles
  # the values will range from x to x + width and y to y + height
  x = 0.
  y = 0.

  # values must be sorted descending (and positive, obviously)
  # values.sort(reverse=True)
  values.sort()
  values = values[::-1]

  # the sum of the values must equal the total area to be laid out
  # i.e., sum(values) == width * height
  values = squarify.normalize_sizes(values, width, height)

  if pad:
    # padded rectangles will probably visualize better for certain cases
    rects = squarify.padded_squarify(values, x, y, width, height)
  else:
    rects = squarify.squarify(values, x, y, width, height)

  return pd.DataFrame(data=rects, index=ids)
