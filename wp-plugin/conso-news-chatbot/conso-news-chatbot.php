<?php
/*
Plugin Name: Conso News Chatbot
Description: Floating chatbot widget that connects to the Conso News FastAPI backend.
Version: 0.1.0
Author: Your Name
*/

if ( ! defined( 'ABSPATH' ) ) {
    exit; // Exit if accessed directly
}

function conso_news_chatbot_enqueue_scripts() {
    // Register the chatbot JS and load it on the frontend
    wp_register_script(
        'conso-news-chatbot',
        plugins_url( 'assets/js/chatbot.js', __FILE__ ),
        array(),          // dependencies (none)
        '0.1.0',
        true              // load in footer
    );

    wp_enqueue_script( 'conso-news-chatbot' );
}
add_action( 'wp_enqueue_scripts', 'conso_news_chatbot_enqueue_scripts' );
