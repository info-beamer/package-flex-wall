[![Import](https://cdn.infobeamer.com/s/img/import.png)](https://info-beamer.com/use?url=https://github.com/info-beamer/package-flex-wall)

A video/image wall with fine grained layout options
===================================================

This video walls allows you to play FullHD content
across any number of screens. You can precisely
control the screen layout of each screen and
even adjust for latency differences between screens.


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

Set a playlist
--------------

Click on the node labeled _Playlist Configuratio_ on the
left side of the configuration screen.

You can add images and video assets to your playlist.
If you make changes to a playlist and click on _Save_, your
devices will go black for a short moment until they are all
back in sync. Therefore it is recommended to make all
changes to a playlist and save only once.

Splitting source videos into smaller chunks
-------------------------------------------

If you have a long video it might make sense to split it up
into smaller parts. That way the player can at each chunk
instead of having to wait for the complete video to end.

You can use ffmpeg for that:

```
ffmpeg -i source.mp4 -c copy -map 0 -segment_time 8 -f segment part%03d.mp4
```

Then import all parts into info-beamer hosted and add them
to the playlist.

Need help?
----------

Right now there's no visual way to set and configure
your screens. Instead you have to manually enter coordinates.

Usually that's not a problem and only has to be done
once. If you need help, feel free to [contact support](https://info-beamer.com/contact).

Release history
---------------

### Version 'beta1'

This is the first public release. While it works, there
might be problems. If you find anything, please open an
issue on [github](https://github.com/info-beamer/package-flex-wall/issues/new).
