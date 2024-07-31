Please install this version of playsound: 1.2.2 \n
```
pip install playsound==1.2.2
```
playsound also needs these two dependencies: GStreamer and PyGObject
Install GStreamer and its Python Bindings
Install GStreamer:
You need to install GStreamer and its plugins. Open your terminal and run:

sh
Copy code
sudo apt-get install gstreamer1.0-plugins-base gstreamer1.0-plugins-good
Install PyGObject:
You also need the Python bindings for GObject. Install it using:

sh
Copy code
sudo apt-get install python3-gi gir1.2-gstreamer-1.0
