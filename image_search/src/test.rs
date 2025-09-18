mod saucenao;
mod headers;

const SAUCENAO_API_KEY: &str = "74741f734355042a56b9422135a65bd09262a147";

#[tokio::main]
async fn main() {
    let saucenao_result = saucenao::search(SAUCENAO_API_KEY, "img.png").await;
    let saucenao_result = match saucenao_result {
        Ok(res) => res,
        Err(e) => {
            eprintln!("Error occurred during search: {}", e);
            return;
        }
    };
    for item in saucenao_result {
        println!("{}", item.display());
    }

}
