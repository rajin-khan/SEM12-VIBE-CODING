functional requirements:

- scan official nsu transcript or image should uploaded scanned and worked
- use csvs or any other form of input of the data
- also need history of all past transcript scans/calls that happened for a specific account
- add google auth (mobile app, webapp, cli)
- add code review/compaction skill or any sort of pipeline that reviews your code and maintains good code quality
- accessible via mobile app, webapp, cli

other requirements:

- work with a minimum of 20 concurrent users (max) [setup automated testing for this]
- 
- OCR/PDF setup for local development:
  - `pip install '.[api,ocr]'`
  - install `tesseract`
  - install Poppler so `pdftoppm` is on PATH
  - use `/audit/ocr-status` to verify the machine is ready before testing PDF/image uploads

- due sunday 8th march
