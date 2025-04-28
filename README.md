# OBSAutomation

**OBSAutomation** is a Python-based automation tool designed to streamline the process of recording Rocket League replays from [Ballchasing.com](https://ballchasing.com), editing them into a single video, and uploading them to YouTube. This project also integrates **BARL** (Broadcast Assistant for Rocket League) and **BakkesMod** to display the scoreboard during the recording, making the replay more professional for broadcasting purposes.

## Features

- **Automated Recording**: Capture Rocket League replays directly from Ballchasing.com with OBS (Open Broadcaster Software).
- **Live Scoreboard**: Display the live Rocket League scoreboard using BARL and BakkesMod during the recording.
- **Video Editing**: Automatically combine the recorded replays into a single edited video.
- **YouTube Upload**: Upload the final edited video to YouTube directly from the script.

## Prerequisites

Before you start, make sure you have the following installed:

- [Python 3.x](https://www.python.org/)
- [OBS Studio](https://obsproject.com/)
- [YouTube Data API v3](https://developers.google.com/youtube/v3) (for uploading videos to YouTube)
- [ffmpeg](https://ffmpeg.org/) (for video editing)
- [BARL (Broadcast Assistant for Rocket League)](https://github.com/Just-Some-BRL-Community/BARL) (for scoreboard display)
- [BakkesMod](https://bakkesmod.com/) (for Rocket League modding and additional features like scoreboard display)