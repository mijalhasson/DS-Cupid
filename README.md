# DS-Cupid
DS Cupid - Technical Assesment for Niutee

## Setup Instructions

### 1. Create a New Conda Environment
```sh
conda create --name myenv python=3.11
conda activate myenv
```

### 2. Install Dependencies
```sh
pip install -r requirements.txt
```

### 3. Download Data
Download the following datasets and save them in the `data/` folder:
- [Dataset 1](https://drive.google.com/file/d/1hKgQ3JwGlMVxdx3c41oas89QoXrsez56/view?usp=drive_link)
- [Dataset 2](https://drive.google.com/file/d/1mLQ3O0ybTfNzJF_eC2nC1PIMBUlsFJI7/view?usp=drive_link)

### 4. Process Room Names
Execute the Jupyter notebook `04_simpler_normalization_methods.ipynb` to process room names and save the reference file into `data/processed/`.

### 5. Run the API
```sh
uvicorn api.main:app
```
#### 5.1 Run the API in dev mode
```sh
uvicorn api.main:app --reload
```

### 6. Access API Documentation (Swagger UI)
Swagger is exposed at `/docs`. If running locally, access it at:
[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### 7. Run Tests
```sh
pytest api/test
```

### 8. View Test Coverage Report
```sh
pytest --cov=api --cov-report=term-missing
```

### 9. Generate Test Coverage Report (HTML)
```sh
pytest --cov=api --cov-report=html
```

