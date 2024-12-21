

hooli

music browser with rating, comments, etc


### pip

we use sqlalchemy


flask-security
flask-seucrity[fsqla]
setuptools
argon2_cffi
sendgrid

flask-migrate
bleach

# ideas

implement folders.  have bands at the top level.  have top songs and albums underneath that.

i mean you don't have to, right?  files could be numbers.  They could be stored in S3 buckets, but if we have a top level of artists then a second level of albums then it'll make more sense to a person who looks from the command line, etc.

create a top-level hierarchy by artist and album

upload files into the html directory hierarchy?

this is good for self-preservation because we could imagine having a lot of files

right now it traverses the directory to find all the files and then sees if they are in the database.

might be better to just look in the database, peruse the files periodically, possible get the mtime of the directory to see if it's necessary.

so someone gets on and createa a new artist

then they create an album

they they upload music

and imagery

the problem with storing the binary images in sqlite is how the webserver can retrieve them and serve them.  i suppose it could be a route in the flask server but it seems like work.

definitely want to be picky about what filenames are acceptable.

do we want to generate our own based off of their file name or maybe title or someting?  probably

i don't want filenames to be like /7/14.wav.  too hard to figure out what's what.

oh also fix the web URLs so we aren't exposing row IDs.  they suck and suck for SEO and understanding what's going on



start or end the directory name with an enforced pattern, like \_dir.  only accept directories as legit for display if the pattern is met.  This makes jailbreaking even harder.

Every media file should have its own dirdctory.

maybe have some kind of metadata file in there that corresponds to the sqlite row 

maybe have a sqlite database in each directory, or something like that

the thing that would be great about that is then directories would be pretty standalone, like renaming or moving it around in the hierarchy wouldn't require, within itself, changing anything.

so if you perused what was underneath your directory and saved it in your sqlite at all, that'd have to be considered temporary or regenerable because we want to freely move stuff around with basically mvdir.

What about having a thing appear in multiple places?  symlinks?  entries into a table?

---

the existing hooli page is pretty cool, where it can play all the files in a directory, etc.

that should probably be the basis of albums and whatever.

but of course really it just shows all the stuff resulting from a select of the media files table.

which is nice.

i have some stuff earlier in the file about media directories driving things that should just be driven by sql queries.

need to do that.

---

was thinking maybe each folder has its on sqlite database containing media_file table with one entry per media file that's like an mp3 or whatever, media_directory table with one row.

when we ingest the folder we copy the rows into our toplevel sql database

that way we can make a zip of a directory and its metadata and it's self-contained

---

it doesn't particularly have to be a hierarchy, you just need a directory with music in it.

but in the URL it should be .../artist/album

i guess it's reasonable to be a hierarchy, but it's arbitrary.  the thing will recursively descend and find all the directories that have sqlite databases, songs and potentially other media.

and then suck all the stuff into a reconstructible top-level mediafiles and media directories.

so you need an editor.  we kind of have one.

all we have to do is move where the database is?


