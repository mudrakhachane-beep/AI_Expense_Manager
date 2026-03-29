import google.generativeai as genai; 
genai.configure(api_key='AIzaSyDvexKaeV4Mq8jswkxWWihO5xTWEs_TjbA'); 
models = genai.list_models(); 
print('Available models:'); 
[print(f'{m.name}: {m.supported_generation_methods}') for m in models]