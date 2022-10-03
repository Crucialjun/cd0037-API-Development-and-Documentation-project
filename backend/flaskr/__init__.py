import random
from flask import Flask, request, abort, jsonify
from flask_cors import CORS
from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10


def paginate_questions(request, selection):
    page = request.args.get("page", 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [book.format() for book in selection]
    current_questions = questions[start:end]

    return current_questions


def create_app(test_config=None):
    app = Flask(__name__)
    setup_db(app)

    """
    Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
    """
    CORS(app)

    """
    Use the after_request decorator to set Access-Control-Allow
    """
    # CORS Headers
    @app.after_request
    def after_request(response):
        response.headers.add(
            "Access-Control-Allow-Headers", "Content-Type,Authorization,true"
        )
        response.headers.add(
            "Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS"
        )
        return response

    """
    Create an endpoint to handle GET requests
    for all available categories.
    """

    @app.route('/categories', methods=['GET'])
    def get_categories():
        selection = Category.query.order_by(Category.type).all()

        if len(selection) == 0:
            abort(404)

        return jsonify({'success': True, 'categories': {
            category.id: category.type for category in selection
        }})

    """
    Create an endpoint to handle GET requests for questions,
    including pagination (every 10 questions).
    This endpoint should return a list of questions,
    number of total questions, current category, categories.
    TEST: At this point, when you start the application
    you should see questions and categories generated,
    ten questions per page and pagination at the bottom of the screen for three pages.
    Clicking on the page numbers should update the questions.
    """
    @app.route('/questions', methods=['GET'])
    def get_questions():
        selection = Question.query.order_by(Question.id).all()

        paginated_questions = paginate_questions(
            request=request, selection=selection)

        categories = Category.query.order_by(Category.type).all()

        if len(paginated_questions) == 0:
            abort(404)

        return jsonify({
            'success': True,
            'questions': paginated_questions,
            'total_questions': len(selection),
            'categories': {category.id: category.type
                           for category in categories},
            'current_category': ""
        })

    """ 
    Create an endpoint to DELETE question using a question ID.
    TEST: When you click the trash icon next to a question, the question will be removed.
    This removal will persist in the database and when you refresh the page.
    """
    @app.route('/questions/<question_id>', methods=['DELETE'])
    def delete_question(question_id):
        try:
            selection = Question.query.get(question_id)

            selection.delete()

            return jsonify({
                'success': True,
                'deleted': question_id
            })
        except BaseException:
            abort(422)

    """
    Create an endpoint to POST a new question,
    which will require the question and answer text,
    category, and difficulty score.
    TEST: When you submit a question on the "Add" tab,
    the form will clear and the question will appear at the end of the last page
    of the questions list in the "List" tab.
    """
    @app.route('/questions', methods=['POST'])
    def create_question():

        body = request.get_json()
        question = body.get('question')
        answer = body.get('answer')
        difficulty = body.get('difficulty')
        category = body.get('category')

        if not (question and answer and difficulty and category):
            abort(422)

        try:
            new_question = Question(question=question,
                                    answer=answer,
                                    difficulty=difficulty,
                                    category=category)

            new_question.insert()

            return jsonify({
                'success': True,
                'created': new_question.id
            })

        except BaseException:
            abort(422)

    """
    Create a POST endpoint to get questions based on a search term.
    It should return any questions for whom the search term
    is a substring of the question.
    TEST: Search by any phrase. The questions list will update to include
    only question that include that string within their question.
    Try using the word "title" to start.
    """
    @app.route('/questions/search', methods=['POST'])
    def search_questions():
        body = request.get_json()

        search_term = body.get('search_term')
        print(search_term)

        if search_term:
            search_results = Question.query.filter(
                Question.question.ilike(f'%{search_term}%')).all()

            return jsonify({
                'success': True,
                'questions': [question.format()
                              for question in search_results],
                'total_questions': len(search_results),
                'current_category': None
            })

        abort(404)

    """
    Create a GET endpoint to get questions based on category.
    TEST: In the "List" tab / main screen, clicking on one of the
    categories in the left column will cause only questions of that
    category to be shown.
    """

    @app.route('/categories/<int:category_id>/questions', methods=['GET'])
    def get_category_questions(category_id):
        selection = Question.query.filter(
            Question.category == category_id).all()

        if len(selection) == 0:
            abort(404)

        return jsonify({
            'success': True,
            'questions': [question.format() for question in selection],
            'total_questions': len(selection),
            'current_category': category_id
        })

    """
    Create a POST endpoint to get questions to play the quiz.
    This endpoint should take category and previous question parameters
    and return a random questions within the given category,
    if provided, and that is not one of the previous questions.
    """

    @app.route('/quiz', methods=['POST'])
    def play_quiz():

        try:
            body = request.get_json()

            if not ('quiz_category' in body and 'previous_questions' in body):
                abort(422)

            category = body.get('quiz_category')
            previous_questions = body.get('previous_questions')

            if category['type'] == 'click':
                available_questions = Question.query.filter(
                    Question.id.notin_(previous_questions)).all()
            else:
                available_questions = Question.query.filter_by(
                    category=category['id']).filter(
                    Question.id.notin_(
                        previous_questions)).all()

            new_question = available_questions[random.randrange(
                0, len(available_questions))].format() if \
                len(available_questions) > 0 else None

            return jsonify({
                'success': True,
                'question': new_question
            })

        except BaseException:
            abort(422)

    """
    Create error handlers for all expected errors
    including 404 and 422.
    """

    @app.errorhandler(404)
    def not_found(error):
        return (
            jsonify({"success": False, "error": 404,
                    "message": "resource not found"}),
            404,
        )

    @app.errorhandler(422)
    def unprocessable(error):
        return (
            jsonify({"success": False, "error": 422,
                    "message": "unprocessable"}),
            422,
        )

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({"success": False, "error": 400, "message": "bad request"}), 400
    return app
