from typing import Optional
import os
import time
import requests
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import cv2

from auto_gangster import gangster

SLACK_BOT_TOKEN=os.environ["SLACK_BOT_TOKEN"]
SLACK_APP_TOKEN=os.environ["SLACK_APP_TOKEN"]

def getImage(url: str, token: str) -> Optional[str]:
    """
    Download the image at `url` to a temporary location, and return the filename
    """
    t = int(time.time())
    resp = requests.get(url, headers={"Authorization": "Bearer %s" % token})
    if resp.status_code == 200:
        fname = f'tmp_{t}.{url.split(".")[-1]}'
        with open(fname, "wb") as fp:
            for chunk in resp:
                fp.write(chunk)
        return fname
    return None


# Install the Slack app and get xoxb- token in advance
app = App(token=SLACK_BOT_TOKEN)


@app.command("/hello-socket-mode")
def hello_command(ack, body):
    user_id = body["user_id"]
    ack(f"Hi, <@{user_id}>!")


@app.event("app_mention")
def event_test(say):
    say("Hi there! Upload an image, and I will make your image look cool 😎")


@app.event("file_shared")
def handle_file_shared_events(event, say):
    image_url = app.client.files_info(file=event["file_id"]).data["file"]["url_private"]

    filename = getImage(image_url, app.client.token)
    if not filename or not os.path.exists(filename):
        print(f"Failed to get image: {filename}")
        return

    try:
        # gangsterfy
        img = cv2.imread(filename)
        n_faces = gangster.make_gangster(img)
        cv2.imwrite(filename, img)

        if n_faces:
            # upload file only if faces detected
            _ = app.client.files_upload(
                channels=say.channel,
                initial_comment="Here's your image, but cooler 😎",
                file=filename,
            )
        else:
            say("No faces found 😢")

    except Exception as e:
        print(f"Exception {e}")
    finally:
        os.remove(filename)


if __name__ == "__main__":
    SocketModeHandler(app, SLACK_APP_TOKEN).start()
