[![Import](https://cdn.infobeamer.com/s/img/import.png)](https://info-beamer.com/use?url=https://github.com/info-beamer/package-flex-wall)

A video/image player with fine grained layout options
===================================================

This package allows you to play FullHD content
across any number of screens. You can precisely
control the screen layout of each screen and
even adjust for latency differences between screens.
Additionally you can also use this package to
place content on only a single screen. Some LED
walls require this as they show only a small area
cropped from a FullHD output.

Multiple devices running the same setup based on
this package will be in sync, so you can also
use this as a synced video/image player for
fullscreen content.

Setting the content area
------------------------

The first thing you have to decide the size of your
content in pixels. If you have 16:9 screens like this:

![Example setup using 3 screens](doc-16x9x3.png)

You content should be in 16:27 (where 27 = 9x3) aspect
ratio. The example size of your content might
therefore be 960x1620. Set this as your content area
width and height.

If you have content of various sizes, you can also
set the content area width/height to some imaginary
value and activate "aspect adjust content". This
will then scale your content into the content
area size while preserving the aspect ratio.

Setting up screens
------------------

First, add the screen you want to use to your account.
Then assign them to your video wall setup.

Finally configure each of your screens by adding them
to the setup configuration. Click on "Add Screen"
for that.

For each screen you can specify which area of the
content area specified above is covered by each of
your screens.

In the example above, the top screen would require
the following configuration values:

```
x = 0, y = 0, width = 960, height = 540
```

These values instruct the video wall to show the top
third of your content on the top screen. Proceed to
set the other screens accordingly.

You can freely choose x, y, width and height values.
As such you can have overlapping screens or compensate
for your screen's bezel.

The rotation value allows you rotate your display around
the chosen screen area. In the example above, you'd
probably only want to use 0 or 180 degree rotation.
If you have portrait mode displays within your wall,
you want the width and height values to reflect their
9:16 aspect ratio.

Finally the latency values allows you to move the
sync point of your screen in relation to each other.
That way you can adjust for minor differences in
the hardware latency of your displays.

Set a playlist
--------------

Click on the node labeled _Playlist Configuration_ on the
left side of the configuration screen.

You can add images and video assets to your playlist.
If you make changes to a playlist and click on _Save_, your
devices will go black for a short moment until they are all
back in sync. Therefore it is recommended to make all
changes to a playlist and save only once.

Playback settings
-----------------

You can have a fade effect between content items. Use the
`Effect` dropdown for that.

Videos cause a 0.5 second gap before they start by default.
Within the 0.5 seconds, info-beamer preloads the video.

You can also select seamless playback. In that case info-beamer
has to load the next video while the previous one is still
playing. This puts a lot of work on the Pi and might not
work in all cases: The previous video might slow down or
skip a few frames. It's recommended that you test your
content to see if seamless mode works correct.

Need help?
----------

Right now there's no visual way to set and configure
your screens. Instead you have to manually enter coordinates.

Usually that's not a problem and only has to be done
once. If you need help, feel free to [contact support](https://info-beamer.com/contact).

Release history
---------------

### Version 2021-02-01

Added audio support

### Version 2019-11-12

Added HEVC video support.

### Version 2019-08-22

Added support for the Pi4.

### Version '0.9'

Added seamless video playback

### Version 'beta1'

This is the first public release. While it works, there
might be problems. If you find anything, please open an
issue on [github](https://github.com/info-beamer/package-flex-wall/issues/new).
