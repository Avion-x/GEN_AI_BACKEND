
# GEN AI API DOCS
#### Here are the api documentation for all the apis in gen ai backend project.
#### All the classes, methods and function have its own doc string, input params and return type included at the same place.



## 1. Generate Test Case API Documentation (Core Engine)
### Overview
The "Generate Test Case" API automates the generation of test cases and scripts for specific devices using AI models. It is designed to enhance efficiency and accuracy in test case creation by leveraging advanced AI technologies and a robust backend processing system.
### URL: {{base_url}}/product/generate_test_cases/
### Input Data Format
The API accepts input in JSON format, comprising the following keys:
- `device_id`: An integer representing the device for which test cases are to be generated.
- `test_type_data`: An array of objects, where each object includes a `test_type_id` and an array of `test_category_ids`.
- `ai_model`: A string specifying the AI model to be used, such as "anthropic.claude-v2".
#### Example Request Payload
```json
{
  "device_id": 6,
  "test_type_data": [
    {
      "test_type_id": 1,
      "test_category_ids": [102]
    }
  ],
  "ai_model": "anthropic.claude-v2"
}
```
### Processing Flow
- **Submission**: A POST request initiates the process with the input data.
- **Immediate Response**: The system immediately responds with a request ID and a processing time message.
- **Backend Processing**:
  - Product prompts are retrieved and customized.
  - Knowledge base prompts and default keywords are fetched.
  - A search in the Pinecone vector database identifies top-k similar items.
  - The Cohere model summarizes these findings.
  - LLM models then generate test cases and scripts based on this summary.
  - The results are parsed and structured for storage.
- **Storage**: The data—prompts, test scripts, and cases—are stored in the `StructuredTestCases` table and committed to a GitHub repository in a new branch specific to the device or test.
### Output
The API's processing is asynchronous, with the initial response including a `request_id` and a message about the processing time. The generated test cases and scripts are stored in a database and a GitHub repository, not immediately returned to the user.

```json
{
    "error": "",
    "status": 200,
    "response": {
        "request_id": "0471cd4943804d0cb81729b7b7420c99",
        "Message": "Processing request will take some time Please come here in 5 mins"
    }
}
```

### Best Practices and Considerations
- **Asynchronous Handling**: Implement client-side mechanisms for status checks or notifications upon completion.
- **Error Handling**: Ensure robust error handling and validation at each step.
- **Security**: Secure the handling and storage of all input and output data, especially when integrating with external systems like GitHub.
- **Scalability**: Design backend processes with scalability in mind to accommodate large data volumes and concurrent requests.
### Conclusion
The "Generate Test Case" API represents a significant advancement in automated test case generation, combining AI models with efficient backend processing to deliver high-quality test cases and scripts. By adhering to the best practices outlined in this documentation, developers can effectively incorporate this API into their testing workflows, thereby enhancing testing efficiency and reliability.



## 2. 