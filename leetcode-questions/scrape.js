const base_url = 'https://www.leetcode.com'

function make_url(path_parts) {
    return [base_url, ...path_parts].join('/');
}

async function async_sleep({seconds}) {
    return new Promise(function (resolve) {
        _.delay(resolve, seconds * 1000)
    });
}

async function with_page({url, f}) {
    let page = window.open(url);
    const seconds_for_page_to_actually_load = 5;
    await async_sleep({seconds: seconds_for_page_to_actually_load});
    const result = f(page);
    page.close();
    return result;
}

class Question_id {
    constructor({url}) {
        this.value = url.split('/')[2]
    }

    get url() {
        return make_url(['problems', this.value]);
    }
};

class Questions_page {
    constructor(number) {
        this.number = number
    }

    get url() {
        return make_url(['problemset', 'all', '?page=' + String(this.number)]);
    }
}

class Question {
    constructor({id, name, tags, description}) {
        this.id = id
        this.name = name
        this.tags = tags
        this.description = description
    }
};

async function question_ids_on_page(questions_page) {
    return await with_page({
        url: questions_page.url,
        f: function(page) {
            return $(page.document).find('[role="rowgroup"]').find('[role="row"]').map(function(index, row) {
                return new Question_id({
                    url: $(row).find('a').first().attr('href')
                });
            });
        }})
}

const seconds_between_requests_to_avoid_getting_rate_limited = 5;
const number_of_questions_pages = parseInt($('.grid').find('[role="navigation"]').find('[aria-label="next"]').prev().text());

const question_ids = await _.range(1, number_of_questions_pages + 1).reduce(async function(question_ids_promise, page_number) {
    const question_ids = await question_ids_promise;
    const questions_page = new Questions_page(page_number);
    const question_ids_on_this_page = await question_ids_on_page(questions_page);
    await async_sleep({seconds: seconds_between_requests_to_avoid_getting_rate_limited});
    return question_ids.concat(...question_ids_on_this_page);
}, []);

async function question_details(question_id) {
    function remove_question_number_from_name(question_name) {
        return question_name.split(' ').slice(1).join(' ');
    }
    return await with_page({
        url: question_id.url,
        f: function(page) {
            const tags_container = $(page.document).find('div:contains("Related Topics")').filter(function() {
                return $(this).children().length === 0;
            });
            tags_container.click();
            const tags = _.map($(page.document).find('.topic-tag__1jni'), function(tag) {
                return tag.text;
            });
            return new Question({
                id: question_id.value,
                name: remove_question_number_from_name($(page.document).find('[data-cy="question-title"]').text()),
                tags: tags,
                description: $(page.document).find('.question-content__JfgR').text(),
            });
        }
    });
}

function download(data, filename, type) {
    var file = new Blob([data], {type: type});
    const url = URL.createObjectURL(file);
    var a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    setTimeout(function() {
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
    }, 0); 
}

await question_ids.reduce(async function(questions_promise, question_id) {
    const questions = await questions_promise;
    const question = await question_details(question_id);
    const formatted_serialized_question = JSON.stringify(question, null, 2);
    download(formatted_serialized_question, question.id + '.json', 'application/json');
    await async_sleep({seconds: seconds_between_requests_to_avoid_getting_rate_limited});
    return [...questions, question]
}, []);
