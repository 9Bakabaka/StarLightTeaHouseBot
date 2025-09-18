use reqwest::{Client, multipart};
use serde_json::Value;
use std::path::Path;
use crate::headers;

const SAUCENAO_ENDPOINT: &str = "https://saucenao.com/search.php";

pub async fn search(api_key: &str, image_path_input: &str) -> Result<Vec<headers::Result>, reqwest::Error> {
    let result_json = fetch(api_key, image_path_input).await?;
    let result_list: Vec<headers::Result> = process(result_json);
    Ok(result_list)
}

async fn fetch(api_key: &str, image_path_input: &str) -> Result<Value, reqwest::Error> {
    // make path std::Path
    let image_path: &Path = Path::new(image_path_input);
    // format multipart
    // if file not found, return error
    let file_part = match multipart::Part::file(image_path).await {
        Ok(part) => part,
        Err(e) => panic!("Failed to read file {}: {}", image_path.display(), e),
    };
    let form = multipart::Form::new()
        .text("output_type", "2")
        .text("api_key", api_key.to_string())
        .part("file", file_part);
    // create client and send request
    println!("Sending request to SauceNAO... ");
    let client = Client::new();
    let result_json: Value = client.post(SAUCENAO_ENDPOINT)
        .multipart(form)
        .send()
        .await?
        .error_for_status()?
        .json()
        .await?;
    /*return*/ Ok(result_json)
}

fn process(result_json: Value) -> Vec<headers::Result> {
    let mut results: Vec<headers::Result> = Vec::new();

    // If json is not valid
    if result_json["results"].as_array().is_none() {
        eprintln!("Invalid JSON structure: 'results' field is missing or not an array.");
        return results; // Return empty vector
    }
    // json -> Vec<Result>
    if let Some(arr) = result_json["results"].as_array() {
        for item in arr {
            // for debug
            // println!("{}", item.to_string());
            // external url may contain multiple links, so convert them into Vec<String> first
            let mut external_urls: Vec<String> = Vec::new();
            for url in item["data"]["ext_urls"].as_array().unwrap_or(&vec![]) {
                external_urls.push(url.to_string().replace("\"", ""));
            }
            let result_item = headers::Result::new(
                item["header"]["similarity"].as_str().unwrap().parse::<f32>().unwrap_or(0.0),
                item["header"]["thumbnail"].to_string().replace("\"", ""),
                external_urls,
                item["data"]["source"].to_string().replace("\"", ""),
                );
            results.push(result_item);
        }
    }
    // order by similarity, descending
    results.sort_by(|small, large| large.similarity.partial_cmp(&small.similarity).unwrap());
    /*return*/ results
}