import time
import shutil
import subprocess
import sys
import os.path
import argparse
from git import Repo, Actor
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler

"""
    FileUpdaterPDF watches for creations and modifications of pdf files at the scheduled source and moves them to the destination.

    Note: The destination should contain the new name if needed. Example: /path/some-new-name.pdf
"""


class FileUpdaterPDF(PatternMatchingEventHandler):
    # Change this to include other specific extensions.
    patterns = ["*.pdf"]

    def __init__(self, author_name, author_email, commit_message, git_directory, destinations):
        """
            Construct a FileUpdaterPDF.
        """
        super(FileUpdaterPDF, self).__init__()
        self.git_directory = git_directory
        self.destinations = destinations
        self.author_name = author_name
        self.author_email = author_email
        self.commit_message = commit_message

    def process(self, event):
        """
            Process files modified or created.

            event.event_type
                'modified' | 'created' | 'moved' | 'deleted'
            event.is_directory
                True | False
            event.src_path
                path/to/observed/file
        """
        # Print path and event type
        print(event.src_path, event.event_type)

        # Copy the file to the destination
        print("Copying files...", end="")
        for destination in self.destinations:
            shutil.copy(event.src_path, destination)
        print("Done")

        # Push to master
        self.git_process()

    def git_process(self):
        """
            Push update to git.
        """
        # Setup Repo.
        print("Getting Index...", end="")
        repo = Repo(self.git_directory)
        index = repo.index
        print("Done")

        # Add files.
        print("Adding files...", end="")
        index.add(self.destinations)
        print("Done")

        # Commit.
        print("Commiting...", end="")
        committer = Actor(self.author_name, self.author_email)
        index.commit(self.commit_message,
                     author=committer, committer=committer)
        print("Done")

        # Push.
        print("Pushing to Git...", end="")
        for remote in repo.remotes:
            if (remote.name == "origin"):
                remote.push()
                break
        print("Done")

    def on_modified(self, event):
        """
            If a file following the patterns defined is modified, execute the following code.
        """
        self.process(event)

    def on_created(self, event):
        """
            If a file following the patterns defined is created, execute the following code.
        """
        self.process(event)


def main():
    # Setup the argument parser.
    parser = argparse.ArgumentParser(
        description="Watch a source directory for PDF modifications or creations, move PDF file to the destination directory, and push to Git")
    parser.add_argument("-n", "--author_name",
                        help="author of the commit", required=True)
    parser.add_argument("-e", "--author_email",
                        help="author's email", required=True)
    parser.add_argument("-m", "--commit_message",
                        help="the message associated with the commit", required=True)
    parser.add_argument("-g", "--git_directory",
                        help="the base Git directory of the destination", required=True)
    parser.add_argument("-s", "--source_path",
                        help="the directory to watch", required=True)
    parser.add_argument("-d", "--destinations",
                        help="the destination(s) of the file", nargs="+")

    # Parse arguments.
    arguments = parser.parse_args()

    # Run WatchDog with FileUpdaterPDF.
    observer = Observer()
    observer.schedule(FileUpdaterPDF(
        arguments.author_name, arguments.author_email, arguments.commit_message, arguments.git_directory, arguments.destinations), arguments.source_path)
    observer.start()

    # Print some initial information.
    print("Ctrl-C to stop")
    print("Observation starting...")

    # Run indefinitely. Stop if Ctrl-C.
    try:
        while(True):
            time.sleep(1)
    except KeyboardInterrupt:
        # Print that it has started quitting information.
        print("Quitting...")
        observer.stop()

    observer.join()


if __name__ == "__main__":
    main()
